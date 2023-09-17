function sendMessage() {
    const phoneNumber = document.getElementById('phoneNumber').value;
    const message = document.getElementById('message').value;
    const url = `https://www.interconectados.net/api2/?phonenumber=${phoneNumber}&text=${encodeURIComponent(message)}&user=demo&password=demo`;

    fetch(url)
        .then(response => response.text())
        .then(data => {
            document.getElementById('response').innerHTML = data;
        });
}

function checkCredits() {
    const url = 'https://www.interconectados.net/api2/get.asp?user=demo&password=demo&get=credits';

    fetch(url)
        .then(response => response.text())
        .then(data => {
            document.getElementById('response').innerHTML = data;
        });
}

function checkStatus() {
    const url = 'https://www.interconectados.net/api2/get.asp?user=demo&password=demo&get=status';

    fetch(url)
        .then(response => response.text())
        .then(data => {
            document.getElementById('response').innerHTML = data;
        });
}

function checkExpiration() {
    const url = 'https://www.interconectados.net/api2/get.asp?user=demo&password=demo&get=expire';

    fetch(url)
        .then(response => response.text())
        .then(data => {
            document.getElementById('response').innerHTML = data;
        });
}
