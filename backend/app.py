from flask import Flask, request, jsonify, render_template, redirect
from flask_cors import CORS
import mysql.connector
import os
import uuid
import time

app = Flask(__name__)
CORS(app)


solicitudes_auth = {}

def get_db_connection():
    """Establece conexión con el contenedor de MySQL utilizando variables de entorno."""
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'user_tienda'),
        password=os.getenv('DB_PASSWORD', 'password_tienda'),
        database=os.getenv('DB_NAME', 'tienda_abarrotes')
    )

@app.route('/', methods=['GET'])
def index():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'], strict_slashes=False)
def login():
    if request.method == 'GET':
        return render_template('index.html')

    data = request.get_json(force=True) or {}
    username = data.get("usuario")
    password = data.get("password")

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            id_solicitud = str(uuid.uuid4())[:6]
            solicitudes_auth[id_solicitud] = {
                "usuario": user["username"],
                "rol": user["rol"],
                "estado": "pendiente"
            }
            return jsonify({
                "status": "success",
                "id_solicitud": id_solicitud,
                "message": "Credenciales correctas. Verifique su dispositivo móvil."
            }), 200
        else:
            return jsonify({"status": "error", "message": "Usuario o contraseña incorrectos"}), 401
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error de base de datos: {str(e)}"}), 500

@app.route('/check-status/<id_solicitud>', methods=['GET'])
def check_status(id_solicitud):
    solicitud = solicitudes_auth.get(id_solicitud)
    if solicitud:
        return jsonify({
            "estado": solicitud["estado"],
            "rol": solicitud["rol"],
            "usuario": solicitud["usuario"]
        }), 200
    return jsonify({"status": "error", "message": "ID no encontrado"}), 404

@app.route('/get-pending', methods=['GET'])
def get_pending():
    for id_sol, datos in solicitudes_auth.items():
        if datos["estado"] == "pendiente":
            return jsonify({"id_solicitud": id_sol, "usuario": datos["usuario"]}), 200
    return jsonify({"id_solicitud": None, "message": "No hay solicitudes"}), 200

@app.route('/autorizar', methods=['POST'])
def autorizar():
    data = request.get_json(force=True) or {}
    id_solicitud = data.get("id_solicitud")
    accion = data.get("accion")
    
    if id_solicitud in solicitudes_auth and accion in ["aprobado", "denegado"]:
        solicitudes_auth[id_solicitud]["estado"] = accion
        return jsonify({"status": "success", "nuevo_estado": accion}), 200
    return jsonify({"status": "error", "message": "Solicitud no válida"}), 400
@app.route('/dashboard', methods=['GET'])
def dashboard():
    rol = request.args.get('rol')
    usuario = request.args.get('usuario')
    if not rol or not usuario:
        return redirect('/login')
    
    if rol == 'Administrador':
        return render_template('dashboard_admin.html', usuario=usuario, rol=rol)
    return render_template('dashboard_cajero.html', usuario=usuario, rol=rol)

@app.route('/inventario', methods=['GET', 'POST'])
def inventario():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
       
        nombre = request.form.get('nombre')
        precio = request.form.get('precio')
        stock = request.form.get('stock')
        categoria = request.form.get('categoria')
        
        if nombre and precio and stock and categoria:
            cursor.execute(
                "INSERT INTO productos (nombre, precio, stock, categoria) VALUES (%s, %s, %s, %s)",
                (nombre, precio, stock, categoria)
            )
            conn.commit()

    cursor.execute("SELECT * FROM productos ORDER BY id DESC")
    productos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('inventario.html', productos=productos)

@app.route('/vender', methods=['GET'])
def vender():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM productos WHERE stock > 0")
    productos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('vender.html', productos=productos)

@app.route('/registrar-empleado', methods=['GET', 'POST'])
def registrar_empleado():
    if request.method == 'POST':
        nombre = request.form.get('nombre_completo')
        username = request.form.get('username')
        password = request.form.get('password')
        rol = request.form.get('rol')
        
        if nombre and username and password and rol:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO usuarios (nombre_completo, username, password, rol) VALUES (%s, %s, %s, %s)",
                (nombre, username, password, rol)
            )
            conn.commit()
            cursor.close()
            conn.close()
            return redirect('/dashboard?rol=Administrador&usuario=admin')

    return render_template('registrar_empleado.html')

# ==========================================
#         LOGICA DEL PUNTO DE VENTA
# ==========================================

@app.route('/procesar-pago', methods=['POST'])
def procesar_pago():
    data = request.get_json(force=True) or {}
    carrito = data.get("productos", []) # Lista de {id, cantidad}
    total = data.get("total", 0)

    if not carrito or total <= 0:
        return jsonify({"status": "error", "message": "El carrito está vacío"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Insertar la venta global
        cursor.execute("INSERT INTO ventas (total) VALUES (%s)", (total,))
        venta_id = cursor.lastrowid

        # 2. Registrar el detalle y descontar inventario por cada producto
        for item in carrito:
            prod_id = item['id']
            cantidad = item['cantidad']
            precio = item['precio']

            # Insertar en el desglose del ticket
            cursor.execute(
                "INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario) VALUES (%s, %s, %s, %s)",
                (venta_id, prod_id, cantidad, precio)
            )

            # Restar del Stock actual en la tabla productos
            cursor.execute(
                "UPDATE productos SET stock = stock - %s WHERE id = %s",
                (cantidad, prod_id)
            )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": "Venta registrada con éxito", "venta_id": venta_id}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al procesar el pago: {str(e)}"}), 500


# ==========================================
#         MÓDULO DEL HISTORIAL
# ==========================================

@app.route('/historial', methods=['GET'])
def historial():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obtenemos las ventas ordenadas por la más reciente
        cursor.execute("SELECT id, DATE_FORMAT(fecha, '%d/%m/%Y %H:%i') as fecha_formateada, total FROM ventas ORDER BY id DESC")
        ventas_registradas = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('historial.html', ventas=ventas_registradas)
    except Exception as e:
        return f"Error al cargar el historial: {str(e)}", 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
