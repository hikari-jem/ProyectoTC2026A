// Configuración de la URL de la API (Flask)
// En desarrollo local puede ser 'http://localhost:5000', pero usando rutas relativas
// o la IP de AWS configurada en el despliegue final.
const API_URL = window.location.origin; 

let statusCheckInterval = null;

document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        // 1. Enviar credenciales a la API
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            // Si el login inicial es correcto, pasamos a esperar la aprobación móvil
            mostrarPantallaEspera();
            iniciarBucleVerificacion(username);
        } else {
            alert(data.message || 'Credenciales incorrectas');
        }

    } catch (error) {
        console.error('Error al conectar con el servidor:', error);
        alert('No se pudo conectar con el servidor de autenticación.');
    }
});

function mostrarPantallaEspera() {
    document.getElementById('login-card').classList.add('hidden');
    document.getElementById('status-card').classList.remove('hidden');
}

function iniciarBucleVerificacion(username) {
    const statusMessage = document.getElementById('status-message');
    const spinner = document.getElementById('loading-spinner');

    // 2. Configurar el setInterval para consultar el estado cada 3 segundos
    statusCheckInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_URL}/check-status?username=${username}`);
            const data = await response.json();

            if (data.status === 'aprobado') {
                clearInterval(statusCheckInterval);
                spinner.classList.add('hidden');
                statusMessage.textContent = '¡Acceso Concedido!';
                statusMessage.className = 'status-text text-approved';
                // Aquí puedes redirigir al usuario si es necesario:
                // window.location.href = "/dashboard.html";
                
            } else if (data.status === 'denegado') {
                clearInterval(statusCheckInterval);
                spinner.classList.add('hidden');
                statusMessage.textContent = 'Acceso Denegado desde el dispositivo móvil.';
                statusMessage.className = 'status-text text-denied';
            }
            // Si el estado sigue siendo 'pendiente', el bucle continúa de forma silenciosa

        } catch (error) {
            console.error('Error consultando el estado de autenticación:', error);
        }
    }, 3000); // 3000 milisegundos = 3 segundos
}