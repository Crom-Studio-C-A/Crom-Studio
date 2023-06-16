// Algoritmo para obtener una Cedula del Registro Civil async function search_cne(rif, nacionalidad, cedula) { try { // Si se pasa el rif como argumento, se extrae la nacionalidad y la cedula if(rif) { nacionalidad = rif[0]; cedula = rif.substr(1)*1; // Se elimina el último dígito del rif que es el verificador }

    // Si no se pasa el rif, se genera a partir de la nacionalidad y la cedula
    if(!rif)
        rif = ci_to_rif(nacionalidad, cedula);

    // Se define la url para hacer la petición GET a la api del CNE
    var url = "http://www.cne.gob.ve/web/registro_civil/buscar_rep.php?nac="+nacionalidad+"&ced="+cedula; // Se usa la variable nacionalidad en lugar de "v"

    // Se usa el módulo fetch para hacer la petición a la api y obtener la respuesta
    var response = await fetch(url);
    var body = await response.text();

    // Se usa el módulo fetch para parsear el cuerpo de la respuesta que es un html
    var parser = new DOMParser();
    var doc = parser.parseFromString(body, "text/html");
    // Se busca el nombre y los apellidos en el html usando selectores de DOM
    var nombre = doc.querySelector('td:nth-child(2)').textContent.trim();
    var apellido = doc.querySelector('td:nth-child(3)').textContent.trim();
    // Se devuelve el nombre y los apellidos como un objeto
    return {nombre: nombre, apellido: apellido};
    catch (err) {
    // Si hay algún error en la ejecución del código o en la respuesta de la api, se devuelve
    return err;
}


// Función para convertir la cédula en un formato válido para la api (rif) function ci_to_rif(nacionalidad, cedula) { var rif = nacionalidad + cedula; var suma = 0; var digito; // Se recorre cada dígito del rif y se multiplica por un factor según su posición for (var i = 0; i < rif.length; i++) { digito = parseInt(rif[i]); // Si es el primer dígito, se asigna un valor según la letra de la nacionalidad if (i == 0) { if (rif[i] == “V”) digito = 1; else if (rif[i] == “E”) digito = 2; else if (rif[i] == “J”) digito = 3; else if (rif[i] == “P”) digito = 4; else if (rif[i] == “G”) digito = 5; } suma += digito * [29, 27, 25, 23, 21, 19, 17, 15, 13][i]; } // Se calcula el resto de dividir la suma entre 11 var resto = suma % 11; // Se calcula el último dígito del rif según el resto var ultimo_digito = resto > 0 ? 11 - resto : resto; return rif + ultimo_digito; }

// Código del formulario const $form = document.querySelector(‘#form’); const buttonSubmit = document.querySelector(‘#submit’); const urlDesktop = ‘https://web.whatsapp.com/’; const urlMobile = ‘whatsapp://’; const phone = ‘584168578289’;

$form.addEventListener("submit", async (event) => { event.preventDefault() buttonSubmit.innerHTML = "<i class=“fas fa-circle-notch fa-spin”></i>’ buttonSubmit.disabled = true

setTimeout(async () => {
    // Se obtienen los valores de los campos del formulario
    let name = document.querySelector('#name').value
    let referencia = document.querySelector('#referencia').value
    let text = document.querySelector('#text').value
    let cedula = document.querySelector('#cedula').value

    // Se llama a la función search_cne con la cédula y se espera el resultado con await
    let data = await search_cne(null, null, cedula);
    
    if (data instanceof Error) {
        // Si hay algún error con la api, se muestra en la consola
        console.error(data);
    } else {
        // Si no hay error, se obtiene el nombre y los apellidos de la data
        let nombre_cne = data.nombre;
        let apellido_cne = data.apellido;

        // Se crea el mensaje de whatsapp con los datos del formulario y de la api
        let message = 'send?phone=' + phone + '&text=*_Formulario De Pago_*%0A*CROM STUDIO*%0A%0A*Nombre*%0A' + name + '%0A*Cedula de Identidad*%0A' + cedula + '%0A*Nombre y Apellido según CNE*%0A' + nombre_cne + ' ' + apellido_cne + '%0A*Referencia*%0A' + referencia + '%0A*Banco*%0A' + text + ''

        // Se abre el enlace de whatsapp según el dispositivo
        if (isMobile()) {
            window.open(urlMobile + message, '_blank')
        } else {
            window.open(urlDesktop + message, '_blank')
        }
    }
    
    buttonSubmit.innerHTML = '<i class="fab fa-whatsapp"></i> Registrar Pago'
    buttonSubmit.disabled = false

}, 4000);
});