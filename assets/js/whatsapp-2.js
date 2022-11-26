

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
        let text = document.querySelector('#text').value
        let message = 'send?phone=' + phone + '&text=Hola, vengo de la pagina web.%0A*CROM STUDIO*%0A%0A*Mi Nombre es:*%0A' + name + '%0A*Mensaje*%0A' + text + ''


        if (isMobile()) {
            window.open(urlMobile + message, '_blank')
        } else {
            window.open(urlDesktop + message, '_blank')
        }

        buttonSubmit.innerHTML = '<i class="fab fa-whatsapp"></i> Enviar Mensaje'
        buttonSubmit.disabled = false

    }, 4000);

});
