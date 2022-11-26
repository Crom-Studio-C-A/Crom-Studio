

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
        let lastname = document.querySelector('#referencia').value
        let email = document.querySelector('#text').value
        let message = 'send?phone=' + phone + '&text=*_Formulario De Pago_*%0A*CROM STUDIO*%0A%0A*Nombre*%0A' + name + '%0A*Referencia*%0A' + referencia + '%0A*Banco*%0A' + text + ''


        if (isMobile()) {
            window.open(urlMobile + message, '_blank')
        } else {
            window.open(urlDesktop + message, '_blank')
        }

        buttonSubmit.innerHTML = '<i class="fab fa-whatsapp"></i> Registrar Pago'
        buttonSubmit.disabled = false

    }, 4000);

});
