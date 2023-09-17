document.getElementById('login-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    // URL para autenticar al usuario con JSONP
    const authURL = `https://www.interconectados.net/api2/get.asp?user=${username}&password=${password}&get=status&callback=handleAuth`;

    // Agregar una función de callback para manejar la respuesta
    window.handleAuth = function(data) {
        if (data.success) {
            // Autenticación exitosa, mostrar el panel de envío de SMS y saldo de créditos
            document.querySelector('.login-container').classList.add('hidden');
            document.querySelector('.sms-container').classList.remove('hidden');
            document.getElementById('credits').classList.remove('hidden');

            // Mostrar el saldo de créditos
            document.getElementById('credits-count').textContent = `${data.credits} créditos disponibles.`;
        } else {
            alert('Error de autenticación. Por favor, verifica tu usuario y contraseña.');
        }
    };

    const script = document.createElement('script');
    script.src = authURL;
    document.head.appendChild(script);
});

document.getElementById('sms-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const phoneNumbers = document.getElementById('phoneNumbers').value;
    const message = document.getElementById('message').value;

    // URL para enviar SMS
    const smsURL = `https://www.interconectados.net/api2/?phonenumber=${phoneNumbers}&text=${message}&user=demo&password=demo`;

    fetch(smsURL)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Mensaje enviado con éxito.');
            } else {
                alert(`Error al enviar el mensaje: ${data.error}`);
            }
        })
        .catch(error => console.error('Error:', error));
});

document.getElementById('check-credits').addEventListener('click', function(event) {
    event.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    // URL para consultar créditos con JSONP
    const creditsURL = `https://www.interconectados.net/api2/get.asp?user=${username}&password=${password}&get=credits&callback=handleCredits`;

    // Agregar una función de callback para manejar la respuesta
    window.handleCredits = function(data) {
        if (data.success) {
            // Mostrar los créditos disponibles
            alert(`${data.credits} créditos disponibles.`);
        } else {
            alert(`Error al consultar los créditos: ${data.error}`);
        }
    };

    const script = document.createElement('script');
    script.src = creditsURL;
    document.head.appendChild(script);
});
