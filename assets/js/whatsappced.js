const $form = document.querySelector('#form');
const buttonSubmit = document.querySelector('#submit');
const urlDesktop = 'https://web.whatsapp.com/';
const urlMobile = 'whatsapp://';
const phone = '584168578289';

$form.addEventListener('submit', (event) => {
    event.preventDefault()
    buttonSubmit.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i>'
    buttonSubmit.disabled = true

    setTimeout(() => {
        let name = document.querySelector('#name').value
        let referencia = document.querySelector('#referencia').value
        let text = document.querySelector('#text').value
        let cedula = document.querySelector('#cedula').value // variable para la casilla de cédula
        let nombre = '' // variable para el nombre de la persona
        let apellido = '' // variable para el apellido de la persona

        // opciones para la petición a la API del CNE
        var get_options = {
          host: 'www.cne.gob.ve',
          port: '80',
          path: "/web/registro_civil/buscar_rep.php?nac=v&ced="+cedula,
          method: 'GET',
          headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
              'Content-Length': 0
          }
        }

 // función para hacer la petición a la API y procesar la respuesta
function consultarCedula(cedula, callback) {
    var proxy = "https://cors-anywhere.herokuapp.com/";
    var url = proxy + "http://www.cne.gob.ve/web/registro_civil/buscar_rep.php?nac=v&ced=" + cedula;
    fetch(url)
      .then(function(response) {
        return response.text();
      })
      .then(function(data) {
        // crear un documento HTML a partir de la respuesta
        var parser = new DOMParser();
        var doc = parser.parseFromString(data, "text/html");
        // obtener las celdas de la tabla
        var cells = doc.querySelectorAll("table td");
        // asignar el nombre y apellido a las variables correspondientes
        nombre = cells[1].textContent;
        apellido = cells[3].textContent;
        callback({nombre: nombre, apellido: apellido});
      })
      .catch(function(error) {
        console.error(error);
      });
  }
  
  
  // llamada a la función con una función callback que asigna el nombre y apellido a las variables correspondientes
  consultarCedula(cedula, function(response) {
    nombre = response.nombre;
    apellido = response.apellido;
  });

        // mensaje de WhatsApp con el nombre y apellido de la persona
        let message = 'send?phone=' + phone + '&text=*_Formulario De Pago_*%0A*CROM STUDIO*%0A%0A*Nombre*%0A' + name + '%0A*Cedula de Identidad*%0A' + cedula + '%0A*Nombre y Apellido*%0A' + nombre + ' ' + apellido + '%0A*Referencia*%0A' + referencia + '%0A*Banco*%0A' + text;


        if (isMobile()) {
            window.open(urlMobile + message, '_blank')
        } else {
            window.open(urlDesktop + message, '_blank')
        }

        buttonSubmit.innerHTML = '<i class="fab fa-whatsapp"></i> Registrar Pago'
        buttonSubmit.disabled = false

    }, 4000);

});