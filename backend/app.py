from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid

app = Flask(__name__)
# Habilitamos CORS para que permita conexiones externas (App Móvil y Web)
CORS(app)

# Base de datos simulada en memoria
# Estructura: { "id_solicitud": {"usuario": "admin", "estado": "pendiente"} }
solicitudes_auth = {}

@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "online", "message": "API de Autenticación 2FA Activa"}), 200

# 1. ENDPOINT PARA EL FRONTEND: Iniciar sesión
@app.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    usuario = data.get("usuario")
    password = data.get("password")
    
    # Credenciales de prueba hardcodeadas para la práctica
    if usuario == "admin" and password == "12345":
        # Generamos un identificador único corto de 6 caracteres para la solicitud
        id_solicitud = str(uuid.uuid4())[:6] 
        solicitudes_auth[id_solicitud] = {"usuario": usuario, "estado": "pendiente"}
        
        return jsonify({
            "status": "success", 
            "id_solicitud": id_solicitud,
            "message": "Sesión retenida. Aprueba desde tu app móvil."
        }), 200
        
    return jsonify({"status": "error", "message": "Usuario o contraseña inválidos"}), 401

# 2. ENDPOINT PARA EL FRONTEND: Consultar si ya aceptaron en el celular
@app.route('/check-status/<id_solicitud>', methods=['GET'])
def check_status(id_solicitud):
    solicitud = solicitudes_auth.get(id_solicitud)
    if solicitud:
        return jsonify({"estado": solicitud["estado"]}), 200
    return jsonify({"status": "error", "message": "ID de solicitud no encontrado"}), 404

# 3. ENDPOINT PARA LA APP MÓVIL: Obtener solicitudes pendientes
@app.route('/get-pending', methods=['GET'])
def get_pending():
    # Buscamos si hay alguna solicitud en estado 'pendiente'
    for id_sol, datos in solicitudes_auth.items():
        if datos["estado"] == "pendiente":
            return jsonify({
                "id_solicitud": id_sol, 
                "usuario": datos["usuario"]
            }), 200
            
    return jsonify({"id_solicitud": None, "message": "No hay solicitudes pendientes"}), 200

# 4. ENDPOINT PARA LA APP MÓVIL: Aprobar o Denegar
@app.route('/autorizar', methods=['POST'])
def autorizar():
    data = request.json or {}
    id_solicitud = data.get("id_solicitud")
    accion = data.get("accion") # Espera 'aprobado' o 'denegado'
    
    if id_solicitud in solicitudes_auth:
        if accion in ["aprobado", "denegado"]:
            solicitudes_auth[id_solicitud]["estado"] = accion
            return jsonify({"status": "success", "nuevo_estado": accion}), 200
        return jsonify({"status": "error", "message": "Acción no válida"}), 400
        
    return jsonify({"status": "error", "message": "Solicitud expirada o no encontrada"}), 404

if __name__ == '__main__':
    # Es crucial que corra en 0.0.0.0 para que Docker pueda redirigir el puerto
    app.run(host='0.0.0.0', port=5000, debug=True)