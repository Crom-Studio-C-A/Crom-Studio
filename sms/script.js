    document.getElementById('loginForm').addEventListener('submit', function(event) {
        event.preventDefault();
    
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
    
        // Realiza la autenticación con tu API
        const authURL = `https://www.interconectados.net/api2/get.asp?user=${username}&password=${password}&get=status`;

        // Supongamos que la autenticación fue exitosa
        const authenticationSuccessful = true;

    if (authenticationSuccessful) {
        // Almacena las credenciales en el almacenamiento local
        localStorage.setItem('username', username);
        localStorage.setItem('password', password);

        // Redirige al usuario al panel de control (dashboard.html)
        window.location.href = 'dashboard.html';
    } else {
        // Maneja el caso en que la autenticación falla
        alert('Credenciales incorrectas. Por favor, inténtalo de nuevo.');
    }
});