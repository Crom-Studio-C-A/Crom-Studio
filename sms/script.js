document.getElementById('loginForm').addEventListener('submit', function(event) {
    event.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    // Construir la URL para la autenticación
    const authURL = `http://www.interconectados.net/api2/get.asp?user=${username}&password=${password}&get=status`;

    // Realizar la solicitud HTTP GET
    fetch(authURL)
        .then(response => response.json())
        .then(data => {
            // Aquí puedes manejar la respuesta de la API
            console.log(data);

            // Redirigir a la siguiente página o realizar otras acciones según la respuesta
        })
        .catch(error => {
            // Manejar errores de la solicitud
            console.error('Error:', error);
        });
});
