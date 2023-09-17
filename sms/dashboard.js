document.getElementById('sendSingleMessage').addEventListener('click', function() {
    // Redirige al usuario a la página para enviar un mensaje a un destinatario individual
    window.location.href = 'sendSingle.html';
});

document.getElementById('sendGroupMessage').addEventListener('click', function() {
    // Redirige al usuario a la página para enviar un mensaje a un grupo
    window.location.href = 'sendGroup.html';
});

document.getElementById('checkCredits').addEventListener('click', function() {
    // Realiza una solicitud para consultar créditos
    // (similar al ejemplo de autenticación en el archivo index.html)
    // ...
});

document.getElementById('checkStatus').addEventListener('click', function() {
    // Realiza una solicitud para consultar el estado de la cuenta
    // (similar al ejemplo de autenticación en el archivo index.html)
    // ...
});

document.getElementById('checkExpiry').addEventListener('click', function() {
    // Realiza una solicitud para consultar la fecha de corte
    // (similar al ejemplo de autenticación en el archivo index.html)
    // ...
});
