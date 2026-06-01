const API_URL = ''; 

let statusCheckInterval = null;

document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Extrayendo estrictamente el .value (texto plano) de los inputs
    const usuario = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();

    try {
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST', 
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ usuario, password }) 
        });

        const data = await response.json();

        if (response.ok && data.status === 'success') {
            mostrarPantallaEspera();
            // Pasamos el ID único de solicitud que generó Flask, NO el objeto HTML
            iniciarBucleVerificacion(data.id_solicitud);
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

function iniciarBucleVerificacion(idSolicitud) {
    const statusMessage = document.getElementById('status-message');
    const spinner = document.getElementById('loading-spinner');

    statusCheckInterval = setInterval(async () => {
        try {
            // Consultamos la ruta limpia /check-status/<id> mapeada en Flask
            const response = await fetch(`${API_URL}/check-status/${idSolicitud}`);
            if (!response.ok) return;
            
            const data = await response.json();

            if (data.estado === 'aprobado') {
                clearInterval(statusCheckInterval);
                if (spinner) spinner.classList.add('hidden');
                statusMessage.textContent = '¡Acceso Concedido!';
                statusMessage.className = 'status-text text-approved';
                
                // Redirección al Dashboard correspondiente según el rol de MySQL
                setTimeout(() => {
                    window.location.href = `/dashboard?rol=${data.rol}&usuario=${data.usuario}`;
                }, 1000);
                
            } else if (data.estado === 'denegado') {
                clearInterval(statusCheckInterval);
                if (spinner) spinner.classList.add('hidden');
                statusMessage.textContent = 'Acceso Denegado desde el dispositivo móvil.';
                statusMessage.className = 'status-text text-denied';
            }

        } catch (error) {
            console.error('Error consultando el estado de autenticación:', error);
        }
    }, 2000); 
}
