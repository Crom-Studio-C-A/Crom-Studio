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

// La lógica para enviar SMS se mantiene igual, ya que es una solicitud POST y no se ve afectada por CORS.
