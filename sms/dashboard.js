document.addEventListener('DOMContentLoaded', function() {
    // Obtén las credenciales del almacenamiento local
    const username = localStorage.getItem('username');
    const password = localStorage.getItem('password');

    // Realiza solicitudes a tu API para obtener información
    fetch(`https://www.interconectados.net/api2/get.asp?user=${username}&password=${password}&get=credits`)
        .then(response => response.json())
        .then(data => {
            // Muestra el saldo disponible en el panel
            document.getElementById('credits').innerText = `Saldo Disponible: ${data.credits}`;
        })
        .catch(error => {
            console.error('Error al obtener créditos:', error);
        });

    fetch(`https://www.interconectados.net/api2/get.asp?user=${username}&password=${password}&get=status`)
        .then(response => response.json())
        .then(data => {
            // Muestra el estado del servicio en el panel
            document.getElementById('status').innerText = `Estado del Servicio: ${data.status}`;
        })
        .catch(error => {
            console.error('Error al obtener estado del servicio:', error);
        });

    fetch(`https://www.interconectados.net/api2/get.asp?user=${username}&password=${password}&get=expire`)
        .then(response => response.json())
        .then(data => {
            // Muestra la fecha de corte en el panel
            document.getElementById('expiry').innerText = `Fecha de Corte: ${data.expire}`;
        })
        .catch(error => {
            console.error('Error al obtener fecha de corte:', error);
        });
});
