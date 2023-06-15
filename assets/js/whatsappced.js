// Algoritmo para obtener una Cedula del Registro Civil
function search_cne(rif, nacionalidad, cedula, res_ced) {
    try {
        if(rif) {
            nacionalidad = rif[0];
            cedula = rif.substr(1, rif.length - 2)*1;
        }

        if(!rif)
            rif = ci_to_rif(nacionalidad, cedula);

        var get_options = {
          host: 'www.cne.gob.ve',
          port: '80',
          path: "/web/registro_civil/buscar_rep.php?nac="+v+"&ced="+cedula,
          method: 'GET',
          headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
              'Content-Length': 0
          }
        };

        // Hacemos la petición a la api y obtenemos la respuesta
        var request = require('request');
        request(get_options, function (error, response, body) {
            if (!error && response.statusCode == 200) {
                // Parseamos el cuerpo de la respuesta que es un html
                var cheerio = require('cheerio');
                var $ = cheerio.load(body);
                // Buscamos el nombre y los apellidos en el html
                var nombre = $('td').eq(1).text().trim();
                var apellido = $('td').eq(2).text().trim();
                // Devolvemos el nombre y los apellidos como un objeto
                res_ced(null, {nombre: nombre, apellido: apellido});
            } else {
                // Si hay algún error, lo devolvemos
                res_ced(error);
            }
        });
    } catch (err) {
        res_ced(err);
    }
}

// Función para convertir la cédula en un formato válido para la api
function ci_to_rif(nacionalidad, cedula) {
    var rif = nacionalidad + cedula;
    var suma = 0;
    var digito;
    for (var i = 0; i < rif.length; i++) {
        digito = parseInt(rif[i]);
        if (i == 0) {
            if (rif[i] == "V") digito = 1;
            else if (rif[i] == "E") digito = 2;
            else if (rif[i] == "J") digito = 3;
            else if (rif[i] == "P") digito = 4;
            else if (rif[i] == "G") digito = 5;
        }
        suma += digito * [29, 27, 25, 23, 21, 19, 17, 15, 13][i];
    }
    var resto = suma % 11;
    var ultimo_digito = resto > 0 ? 11 - resto : resto;
    return rif + ultimo_digito;
}

// Código del formulario
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
        let cedula = document.querySelector('#cedula').value

        // Llamamos a la función search_cne con la cédula y una función callback
        search_cne(null, null, cedula, function(error, data) {
            if (error) {
                // Si hay algún error con la api, lo mostramos en la consola
                console.error(error);
            } else {
                // Si no hay error, obtenemos el nombre y los apellidos de la data
                let nombre_cne = data.nombre;
                let apellido_cne = data.apellido;

                // Creamos el mensaje de whatsapp con los datos del formulario y de la api
                let message = 'send?phone=' + phone + '&text=*_Formulario De Pago_*%0A*CROM STUDIO*%0A%0A*Nombre*%0A' + name + '%0A*Cedula de Identidad*%0A' + cedula + '%0A*Nombre y Apellido según CNE*%0A' + nombre_cne + ' ' + apellido_cne + '%0A*Referencia*%0A' + referencia + '%0A*Banco*%0A' + text + ''

                // Abrimos el enlace de whatsapp según el dispositivo
                if (isMobile()) {
                    window.open(urlMobile + message, '_blank')
                } else {
                    window.open(urlDesktop + message, '_blank')
                }
            }
        });

        buttonSubmit.innerHTML = '<i class="fab fa-whatsapp"></i> Registrar Pago'
        buttonSubmit.disabled = false

    }, 4000);

});