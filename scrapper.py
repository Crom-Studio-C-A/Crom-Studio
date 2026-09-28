import sys
import os
import sqlite3
import csv
import json
import requests
import whois
import re
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLineEdit, QLabel, QTableWidget, QTableWidgetItem, 
                             QTabWidget, QMessageBox, QHeaderView, QComboBox, QCheckBox, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# =======================================================
# 1. GESTIÓN DE BASES DE DATOS (SQLite)
# =======================================================

class DatabaseManager:
    def __init__(self):
        self.init_domain_db()
        self.init_client_db()

    def init_domain_db(self):
        conn = sqlite3.connect('domains_data.db')
        cursor = conn.cursor()
        # Tabla para SSL (crt.sh)
        cursor.execute('''CREATE TABLE IF NOT EXISTS ssl_certs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            domain_query TEXT,
                            issuer_ca TEXT,
                            name_value TEXT,
                            not_before TEXT,
                            not_after TEXT UNIQUE)''')
        # Tabla para WHOIS
        cursor.execute('''CREATE TABLE IF NOT EXISTS whois_info (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            domain TEXT UNIQUE,
                            registrar TEXT,
                            creation_date TEXT,
                            emails TEXT,
                            org TEXT)''')
        conn.commit()
        conn.close()

    def init_client_db(self):
        conn = sqlite3.connect('clients_data.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS clients (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT,
                            phone TEXT,
                            whatsapp TEXT,
                            website TEXT,
                            social_media TEXT,
                            address TEXT,
                            source TEXT,
                            UNIQUE(name, phone))''')
        conn.commit()
        conn.close()

db_manager = DatabaseManager()

# =======================================================
# 2. HILOS DE SCRAPING (Para no congelar la GUI)
# =======================================================

class CrtShWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, query):
        super().__init__()
        self.query = query

    def run(self):
        try:
            self.progress.emit(10)
            url = f"https://crt.sh/?q={self.query}&output=json"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(url, headers=headers, timeout=20)
            self.progress.emit(50)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                conn = sqlite3.connect('domains_data.db')
                cursor = conn.cursor()
                
                for item in data:
                    issuer = item.get('issuer_name', '').split('O=')[-1].split(',')[0]
                    name_value = item.get('name_value', '')
                    not_before = item.get('not_before', '')
                    not_after = item.get('not_after', '')
                    
                    try:
                        cursor.execute('''INSERT OR IGNORE INTO ssl_certs 
                                          (domain_query, issuer_ca, name_value, not_before, not_after) 
                                          VALUES (?, ?, ?, ?, ?)''', 
                                       (self.query, issuer, name_value, not_before, not_after))
                    except sqlite3.IntegrityError:
                        pass
                        
                    results.append((issuer, name_value, not_before, not_after))
                
                conn.commit()
                conn.close()
                self.progress.emit(100)
                self.finished.emit(results)
            else:
                self.error.emit(f"Error HTTP {response.status_code}. crt.sh puede estar saturado.")
        except Exception as e:
            self.error.emit(str(e))

class WhoisWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, domain):
        super().__init__()
        self.domain = domain

    def run(self):
        try:
            w = whois.whois(self.domain)
            
            # Limpiar datos
            registrar = w.registrar if isinstance(w.registrar, str) else str(w.registrar)
            creation = str(w.creation_date[0]) if isinstance(w.creation_date, list) else str(w.creation_date)
            emails = str(w.emails[0]) if isinstance(w.emails, list) else str(w.emails)
            org = w.org if isinstance(w.org, str) else str(w.org)

            conn = sqlite3.connect('domains_data.db')
            cursor = conn.cursor()
            cursor.execute('''INSERT OR REPLACE INTO whois_info (domain, registrar, creation_date, emails, org) 
                              VALUES (?, ?, ?, ?, ?)''', (self.domain, registrar, creation, emails, org))
            conn.commit()
            conn.close()
            
            self.finished.emit({'registrar': registrar, 'creation': creation, 'emails': emails, 'org': org})
        except Exception as e:
            self.error.emit(f"No se pudo obtener WHOIS: {str(e)}")

class ClientScraperWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, city, business_type):
        super().__init__()
        self.city = city
        self.business_type = business_type

    def run(self):
        self.progress.emit(5)
        all_results = []
        
        # 1. OpenStreetMap (Overpass API)
        try:
            all_results.extend(self._scrape_osm())
        except Exception as e:
            print(f"Error OSM: {e}")
        self.progress.emit(20)
        
        # 2. Infoguia.com
        try:
            all_results.extend(self._scrape_infoguia())
        except Exception as e:
            print(f"Error Infoguia: {e}")
        self.progress.emit(40)
        
        # 3. Mappi.com.ve
        try:
            all_results.extend(self._scrape_mappi())
        except Exception as e:
            print(f"Error Mappi: {e}")
        self.progress.emit(60)
        
        # 4. Cylex.com.ve
        try:
            all_results.extend(self._scrape_cylex())
        except Exception as e:
            print(f"Error Cylex: {e}")
        self.progress.emit(80)

        # 5. Google Maps (Scraping local sin API)
        try:
            all_results.extend(self._scrape_google_basic())
        except Exception as e:
            print(f"Error Google: {e}")
        self.progress.emit(90)
        
        # Guardar en DB y preparar para UI
        saved_results = []
        try:
            conn = sqlite3.connect('clients_data.db')
            cursor = conn.cursor()
            for r in all_results:
                name, phone, whatsapp, website, social_media, address, source = r
                if name and (phone or whatsapp or website or social_media):
                    try:
                        cursor.execute('''INSERT OR IGNORE INTO clients (name, phone, whatsapp, website, social_media, address, source) 
                                          VALUES (?, ?, ?, ?, ?, ?, ?)''', r)
                        saved_results.append((name, phone, whatsapp, website, social_media, address))
                    except sqlite3.IntegrityError:
                        pass
            conn.commit()
            conn.close()
        except Exception as e:
            self.error.emit(f"Error base de datos: {str(e)}")

        self.progress.emit(100)
        self.finished.emit(saved_results)

    def _generic_parse(self, html, source_name):
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        # Busca contenedores comunes de resultados en diferentes directorios y Google
        for item in soup.find_all(['div', 'article', 'li'], class_=lambda x: x and any(c in x.lower() for c in ['item', 'card', 'result', 'row', 'box', 'company', 'g '])):
            name_tag = item.find(['h2', 'h3', 'h4', 'strong'])
            if not name_tag: continue
            
            name = name_tag.text.strip()
            if not name or len(name) < 3: continue
            
            phone, whatsapp, website, social_media, address = '', '', '', '', self.city
            
            for a in item.find_all('a', href=True):
                href = a['href'].lower()
                if 'tel:' in href: phone = href.replace('tel:', '').strip()
                elif 'wa.me' in href or 'api.whatsapp' in href: whatsapp = href
                elif 'facebook.com' in href: social_media += f"FB: {href} "
                elif 'instagram.com' in href: social_media += f"IG: {href} "
                elif 'http' in href and not any(d in href for d in ['infoguia', 'mappi', 'cylex', 'google', 'w3']):
                    website = a['href']
            
            # Expresión regular inteligente para atrapar teléfonos en texto plano
            if not phone:
                text_content = item.get_text(separator=' ')
                phone_match = re.search(r'(\+?\d{2,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4})', text_content)
                if phone_match: phone = phone_match.group(1).strip()
            
            addr_tag = item.find(['address', 'p', 'span'], class_=lambda x: x and ('dir' in x.lower() or 'address' in x.lower() or 'loc' in x.lower()))
            if addr_tag: address = addr_tag.text.strip()
            
            results.append((name, phone, whatsapp, website, social_media, address, source_name))
        return results

    def _scrape_osm(self):
        results = []
        time.sleep(random.uniform(1.5, 3.0))
        overpass_url = "http://overpass-api.de/api/interpreter"
        query = f"""
        [out:json][timeout:25];
        area[name="{self.city}"]->.searchArea;
        (
          node["amenity"="{self.business_type}"](area.searchArea);
          way["amenity"="{self.business_type}"](area.searchArea);
          node["shop"="{self.business_type}"](area.searchArea);
        );
        out center;
        """
        response = requests.post(overpass_url, data={'data': query}, timeout=30)
        if response.status_code == 200:
            data = response.json()
            for element in data.get('elements', []):
                tags = element.get('tags', {})
                name = tags.get('name')
                phone = tags.get('phone') or tags.get('contact:phone') or ''
                whatsapp = tags.get('contact:whatsapp') or ''
                website = tags.get('website') or tags.get('contact:website') or ''
                
                facebook = tags.get('contact:facebook') or tags.get('facebook') or ''
                instagram = tags.get('contact:instagram') or tags.get('instagram') or ''
                social_media = ""
                if facebook: social_media += f"FB: {facebook} "
                if instagram: social_media += f"IG: {instagram}"
                
                addr = f"{tags.get('addr:street', '')} {tags.get('addr:housenumber', '')}".strip()
                if not addr: addr = self.city
                
                if name:
                    results.append((name, str(phone), str(whatsapp), str(website), social_media, addr, 'OSM'))
        return results

    def _scrape_infoguia(self):
        results = []
        page = 1
        while page <= 4:
            time.sleep(random.uniform(2.5, 5.0)) # Retardo para evitar baneos
            url = f"https://infoguia.com/busqueda.asp?txt={quote_plus(self.business_type)}+{quote_plus(self.city)}&est=100&pag={page}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            try:
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code != 200: break
                page_results = self._generic_parse(response.text, 'Infoguia')
                if not page_results: break
                results.extend(page_results)
            except: break
            page += 1
        return results

    def _scrape_mappi(self):
        results = []
        page = 1
        while page <= 4:
            time.sleep(random.uniform(2.5, 5.0))
            url = f"https://mappi.com.ve/lista-de-anuncios/?type=place&search_keywords={quote_plus(self.business_type)}&region={quote_plus(self.city)}&sort=latest"
            if page > 1: url += f"&page={page}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            try:
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code != 200: break
                page_results = self._generic_parse(response.text, 'Mappi')
                if not page_results: break
                results.extend(page_results)
            except: break
            page += 1
        return results

    def _scrape_cylex(self):
        results = []
        page = 1
        while page <= 4:
            time.sleep(random.uniform(3.0, 5.5))
            url = f"https://www.cylex.com.ve/s?q={quote_plus(self.business_type)}&c={quote_plus(self.city)}&p={page}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            try:
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code != 200: break
                page_results = self._generic_parse(response.text, 'Cylex')
                if not page_results: break
                results.extend(page_results)
            except: break
            page += 1
        return results

    def _scrape_google_basic(self):
        results = []
        # Delay alto porque Google bloquea rápidamente sin API
        time.sleep(random.uniform(4.0, 8.0))
        url = f"https://www.google.com/search?q={quote_plus(self.business_type)}+en+{quote_plus(self.city)}&hl=es"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                # Nuestro _generic_parse es suficientemente inteligente para sacar los locales de Google
                results.extend(self._generic_parse(response.text, 'Google SERP'))
        except Exception as e:
            print(f"Error Google: {e}")
        return results

# =======================================================
# 3. INTERFAZ GRÁFICA (GUI)
# =======================================================

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.fig.patch.set_facecolor('#2b2b2b') # Fondo oscuro
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor('#2b2b2b')
        self.axes.tick_params(colors='white')
        self.axes.xaxis.label.set_color('white')
        self.axes.yaxis.label.set_color('white')
        super(MplCanvas, self).__init__(self.fig)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scraper Master Pro - OSINT & Leads")
        self.setGeometry(100, 100, 1100, 750)
        self.apply_dark_theme()

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.setup_domain_tab()
        self.setup_client_tab()

    def apply_dark_theme(self):
        dark_stylesheet = """
        QMainWindow { background-color: #1e1e1e; }
        QTabWidget::pane { border: 1px solid #444; background: #1e1e1e; }
        QTabBar::tab { background: #2d2d2d; color: #fff; padding: 10px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
        QTabBar::tab:selected { background: #007acc; font-weight: bold; }
        QWidget { color: #ffffff; background-color: #1e1e1e; }
        QPushButton { background-color: #007acc; color: white; border-radius: 5px; padding: 8px; font-weight: bold; }
        QPushButton:hover { background-color: #005f9e; }
        QLineEdit, QComboBox { background-color: #2d2d2d; border: 1px solid #555; padding: 6px; border-radius: 4px; color: white;}
        QTableWidget { background-color: #2d2d2d; gridline-color: #444; color: white; border: none; }
        QHeaderView::section { background-color: #3d3d3d; padding: 4px; border: 1px solid #222; font-weight: bold; }
        QProgressBar { text-align: center; border: 1px solid #444; border-radius: 5px; background: #2d2d2d; }
        QProgressBar::chunk { background-color: #007acc; width: 20px; }
        """
        self.setStyleSheet(dark_stylesheet)

    # --- PESTAÑA 1: DOMINIOS ---
    def setup_domain_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Controles superiores
        control_layout = QHBoxLayout()
        self.domain_input = QLineEdit()
        self.domain_input.setPlaceholderText("Ej: %.com.ve o %.gob.ve para masivos")
        
        btn_crtsh = QPushButton("🔍 Escanear Subdominios (crt.sh)")
        btn_crtsh.clicked.connect(self.run_crtsh_scan)
        
        btn_whois = QPushButton("🌐 Info WHOIS")
        btn_whois.clicked.connect(self.run_whois_scan)
        
        btn_export = QPushButton("💾 Exportar DB Dominios")
        btn_export.clicked.connect(self.export_domains)

        control_layout.addWidget(QLabel("Dominio/Query:"))
        control_layout.addWidget(self.domain_input)
        control_layout.addWidget(btn_crtsh)
        control_layout.addWidget(btn_whois)
        control_layout.addWidget(btn_export)

        # Progreso
        self.domain_progress = QProgressBar()
        self.domain_progress.setValue(0)
        self.domain_progress.hide()

        # Área Central: Tabla y Gráfico
        content_layout = QHBoxLayout()
        
        self.domain_table = QTableWidget(0, 4)
        self.domain_table.setHorizontalHeaderLabels(["Autoridad (CA)", "Subdominio", "Válido Desde", "Válido Hasta"])
        self.domain_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        self.domain_chart = MplCanvas(self, width=4, height=4, dpi=100)

        content_layout.addWidget(self.domain_table, stretch=2)
        content_layout.addWidget(self.domain_chart, stretch=1)

        # Detalles WHOIS
        self.whois_label = QLabel("Resultados WHOIS aparecerán aquí...")
        self.whois_label.setStyleSheet("background-color: #2d2d2d; padding: 10px; border-radius: 5px;")
        self.whois_label.setWordWrap(True)

        layout.addLayout(control_layout)
        layout.addWidget(self.domain_progress)
        layout.addLayout(content_layout)
        layout.addWidget(self.whois_label)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "🌐 Análisis de Dominios & SSL")
        
        self.load_domain_db_to_table()

    # --- PESTAÑA 2: CLIENTES ---
    def setup_client_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        control_layout = QHBoxLayout()
        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("Ej: Maracaibo")
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["restaurant", "clinic", "hospital", "dentist", "pharmacy", "cafe", "car_repair"])
        
        btn_scrape_clients = QPushButton("🤖 Buscar Clientes (Sin API)")
        btn_scrape_clients.clicked.connect(self.run_client_scrape)
        
        btn_export_clients = QPushButton("💾 Exportar Leads")
        btn_export_clients.clicked.connect(self.export_clients)

        control_layout.addWidget(QLabel("Ciudad:"))
        control_layout.addWidget(self.city_input)
        control_layout.addWidget(QLabel("Tipo Negocio:"))
        control_layout.addWidget(self.type_combo)
        control_layout.addWidget(btn_scrape_clients)
        control_layout.addWidget(btn_export_clients)

        # Filtros
        filter_layout = QHBoxLayout()
        self.chk_phone = QCheckBox("Solo con Teléfono")
        self.chk_phone.stateChanged.connect(self.load_client_db_to_table)
        self.chk_web = QCheckBox("Solo con Web")
        self.chk_web.stateChanged.connect(self.load_client_db_to_table)
        filter_layout.addWidget(self.chk_phone)
        filter_layout.addWidget(self.chk_web)
        filter_layout.addStretch()

        self.client_progress = QProgressBar()
        self.client_progress.setValue(0)
        self.client_progress.hide()

        content_layout = QHBoxLayout()
        self.client_table = QTableWidget(0, 6)
        self.client_table.setHorizontalHeaderLabels(["Nombre Empresa", "Teléfono", "WhatsApp", "Página Web", "Redes Sociales", "Dirección"])
        self.client_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        self.client_chart = MplCanvas(self, width=4, height=4, dpi=100)

        content_layout.addWidget(self.client_table, stretch=2)
        content_layout.addWidget(self.client_chart, stretch=1)

        layout.addLayout(control_layout)
        layout.addLayout(filter_layout)
        layout.addWidget(self.client_progress)
        layout.addLayout(content_layout)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "👥 Scraper de Directorios & Leads")
        
        self.load_client_db_to_table()

    # =======================================================
    # FUNCIONES LÓGICAS - DOMINIOS
    # =======================================================
    def run_crtsh_scan(self):
        query = self.domain_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Error", "Ingresa un dominio para buscar.")
            return
        
        self.domain_progress.show()
        self.crt_worker = CrtShWorker(query)
        self.crt_worker.progress.connect(self.domain_progress.setValue)
        self.crt_worker.finished.connect(self.on_crtsh_finished)
        self.crt_worker.error.connect(self.on_worker_error)
        self.crt_worker.start()

    def on_crtsh_finished(self, results):
        self.domain_progress.hide()
        QMessageBox.information(self, "Éxito", f"Se encontraron {len(results)} certificados/subdominios.")
        self.load_domain_db_to_table()
        self.update_domain_chart()

    def run_whois_scan(self):
        domain = self.domain_input.text().strip()
        if not domain: return
        self.whois_worker = WhoisWorker(domain)
        self.whois_worker.finished.connect(self.on_whois_finished)
        self.whois_worker.error.connect(self.on_worker_error)
        self.whois_worker.start()

    def on_whois_finished(self, data):
        info = f"<b>Registrador:</b> {data['registrar']} | <b>Creado:</b> {data['creation']} <br>"
        info += f"<b>Emails:</b> {data['emails']} | <b>Org:</b> {data['org']}"
        conn = sqlite3.connect('domains_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM whois_info WHERE org=? AND org!='None'", (data['org'],))
        count = cursor.fetchone()[0]
        conn.close()
        info += f"<br><br><i>Estadística local: Esta organización ({data['org']}) tiene {count} dominios registrados en nuestra DB.</i>"
        self.whois_label.setText(info)

    def load_domain_db_to_table(self):
        conn = sqlite3.connect('domains_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT issuer_ca, name_value, not_before, not_after FROM ssl_certs ORDER BY id DESC LIMIT 200")
        rows = cursor.fetchall()
        conn.close()

        self.domain_table.setRowCount(0)
        for row_idx, row_data in enumerate(rows):
            self.domain_table.insertRow(row_idx)
            for col_idx, col_data in enumerate(row_data):
                self.domain_table.setItem(row_idx, col_idx, QTableWidgetItem(str(col_data)))
        self.update_domain_chart()

    def update_domain_chart(self):
        conn = sqlite3.connect('domains_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT issuer_ca, COUNT(*) FROM ssl_certs GROUP BY issuer_ca ORDER BY COUNT(*) DESC LIMIT 5")
        data = cursor.fetchall()
        conn.close()

        self.domain_chart.axes.clear()
        if data:
            labels = [str(i[0])[:15]+".." for i in data]
            sizes = [i[1] for i in data]
            # Grafico circular bonito
            wedges, texts, autotexts = self.domain_chart.axes.pie(
                sizes, labels=labels, autopct='%1.1f%%', 
                textprops=dict(color="w"), colors=['#007acc', '#0098ff', '#33aaff', '#66ccff', '#99ddff']
            )
            self.domain_chart.axes.set_title("Top 5 Autoridades Certificadoras (CAs)", color='white')
        self.domain_chart.draw()

    def export_domains(self):
        self._export_to_csv('domains_data.db', 'ssl_certs', 'export_dominios.csv')

    # =======================================================
    # FUNCIONES LÓGICAS - CLIENTES
    # =======================================================
    def run_client_scrape(self):
        city = self.city_input.text().strip()
        b_type = self.type_combo.currentText()
        if not city:
            QMessageBox.warning(self, "Error", "Ingresa una ciudad (Ej: Caracas).")
            return
            
        self.client_progress.show()
        self.client_worker = ClientScraperWorker(city, b_type)
        self.client_worker.progress.connect(self.client_progress.setValue)
        self.client_worker.finished.connect(self.on_client_finished)
        self.client_worker.error.connect(self.on_worker_error)
        self.client_worker.start()

    def on_client_finished(self, results):
        self.client_progress.hide()
        QMessageBox.information(self, "Éxito", f"Se extrajeron {len(results)} empresas con datos de contacto.")
        self.load_client_db_to_table()

    def load_client_db_to_table(self):
        conn = sqlite3.connect('clients_data.db')
        cursor = conn.cursor()
        
        query = "SELECT name, phone, whatsapp, website, social_media, address FROM clients WHERE 1=1"
        if self.chk_phone.isChecked(): query += " AND (phone != '' OR whatsapp != '')"
        if self.chk_web.isChecked(): query += " AND (website != '' OR social_media != '')"
        query += " ORDER BY id DESC LIMIT 500"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        self.client_table.setRowCount(0)
        for row_idx, row_data in enumerate(rows):
            self.client_table.insertRow(row_idx)
            for col_idx, col_data in enumerate(row_data):
                val = str(col_data)
                if val == 'None': val = '---'
                self.client_table.setItem(row_idx, col_idx, QTableWidgetItem(val))
        self.update_client_chart()

    def update_client_chart(self):
        conn = sqlite3.connect('clients_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM clients")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM clients WHERE phone != '' OR whatsapp != ''")
        with_phone = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM clients WHERE website != '' OR social_media != ''")
        with_web = cursor.fetchone()[0]
        conn.close()

        self.client_chart.axes.clear()
        categories = ['Total', 'Con Teléfono/WA', 'Con Web/Redes']
        values = [total, with_phone, with_web]
        
        self.client_chart.axes.bar(categories, values, color=['#9c27b0', '#4CAF50', '#2196F3'])
        self.client_chart.axes.set_title("Estadísticas de Contacto Leads", color='white')
        self.client_chart.draw()

    def export_clients(self):
        self._export_to_csv('clients_data.db', 'clients', 'export_clientes_leads.csv')

    # =======================================================
    # UTILIDADES
    # =======================================================
    def on_worker_error(self, err_msg):
        self.domain_progress.hide()
        self.client_progress.hide()
        QMessageBox.critical(self, "Error en la operación", err_msg)

    def _export_to_csv(self, db_name, table_name, file_name):
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            # Obtener nombres de columnas
            col_names = [description[0] for description in cursor.description]
            
            with open(file_name, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(col_names)
                writer.writerows(rows)
            conn.close()
            QMessageBox.information(self, "Exportado", f"Datos exportados exitosamente a {file_name} en la carpeta actual.")
        except Exception as e:
            QMessageBox.critical(self, "Error al exportar", str(e))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion') # Estilo base para que el CSS oscuro aplique bien
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())