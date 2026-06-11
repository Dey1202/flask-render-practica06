import os
from flask import Flask, request, redirect, url_for, render_template_string
from datetime import datetime

try:
    import psycopg2
    import psycopg2.extras
    USAR_DB = True
except ImportError:
    USAR_DB = False

app = Flask(__name__)

# OBTENER URL DE LA BASE DE DATOS
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# CORRECCIÓN AUTOMÁTICA DE FORMATO DE URL PARA EVITAR ERRORES
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def get_db():
    """Conectar a PostgreSQL de forma directa"""
    if not DATABASE_URL:
        return None
    try:
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=5)
        return conn
    except Exception as e:
        print(f"Error de conexión: {e}")
        return None

def init_db():
    """Crear tabla si no existe"""
    conn = get_db()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS comentarios (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL,
                    campus VARCHAR(100),
                    comentario TEXT NOT NULL,
                    fecha TIMESTAMP DEFAULT NOW()
                )
            """)
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error al inicializar tabla: {e}")

def obtener_comentarios():
    """Leer comentarios de la base de datos"""
    conn = get_db()
    if not conn:
        return []
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM comentarios ORDER BY fecha DESC LIMIT 50")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"Error al obtener comentarios: {e}")
        return []

def guardar_comentario(nombre, campus, comentario):
    """Guardar un comentario en la base de datos"""
    conn = get_db()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO comentarios (nombre, campus, comentario) VALUES (%s, %s, %s)",
            (nombre, campus, comentario)
        )
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error al guardar comentario: {e}")
        return False

TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Práctica 06 - PaaS Render</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            color: #eee;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 750px; margin: 0 auto; }
        h1 {
            text-align: center;
            margin: 20px 0;
            background: linear-gradient(90deg, #7f5af0, #2cb67d);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2em;
        }
        .badge {
            display: inline-block;
            background: #7f5af0;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.8em;
            margin: 2px;
        }
        .info-box {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 20px;
            margin: 15px 0;
        }
        .info-box h3 { color: #2cb67d; margin-bottom: 10px; }
        form {
            background: rgba(255,255,255,0.08);
            padding: 20px;
            border-radius: 12px;
            margin: 15px 0;
        }
        input, textarea, select {
            width: 100%;
            padding: 10px;
            margin: 8px 0;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            background: rgba(255,255,255,0.05);
            color: #eee;
            font-size: 1em;
        }
        button {
            background: #2cb67d;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            width: 100%;
            font-weight: bold;
        }
        button:hover { background: #249666; }
        .comment {
            background: rgba(255,255,255,0.05);
            padding: 15px;
            border-radius: 8px;
            margin: 8px 0;
            border-left: 3px solid #7f5af0;
        }
        .meta {
            font-size: 0.8em;
            color: #888;
            margin-top: 8px;
        }
        .status {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 5px;
        }
        .status.ok { background: #2cb67d; }
        .status.off { background: #e53170; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Servicios en la Nube - PaaS</h1>
        <p style="text-align:center">
            <span class="badge">Render.com</span>
            <span class="badge">Flask</span>
            <span class="badge">PostgreSQL</span>
            <span class="badge">PaaS</span>
        </p>

        <div class="info-box">
            <h3>Estado del Sistema</h3>
            <p><span class="status {{ 'ok' if db_ok else 'off' }}"></span> Base de datos: {{ 'Conectada (PostgreSQL) 🟢' if db_ok else 'No disponible 🔴' }}</p>
            <p><span class="status ok"></span> Servidor: Render Web Service</p>
            <p><span class="status ok"></span> Deploy: Automático desde GitHub (CD)</p>
        </div>

        <h2>Muro de Comentarios</h2>
        
        <form method="POST" action="/">
            <input name="nombre" placeholder="Tu nombre" required>
            <select name="campus">
                <option value="TecNM Tampico">TecNM Tampico</option>
                <option value="TecNM Ciudad Madero">TecNM Ciudad Madero</option>
                <option value="TecNM Altamira">TecNM Altamira</option>
                <option value="TecNM Pánuco">TecNM Pánuco</option>
                <option value="Otro">Otro</option>
            </select>
            <textarea name="comentario" placeholder="Escribe un comentario..." rows="3" required></textarea>
            <button type="submit">Publicar Comentario</button>
        </form>

        <h3 style="margin:15px 0">Comentarios Guardados ({{ comentarios|length }})</h3>
        {% for c in comentarios %}
        <div class="comment">
            <strong>{{ c.nombre }}</strong> - <span style="color:#2cb67d">{{ c.campus }}</span>
            <p style="margin-top:5px; color:#ddd;">{{ c.comentario }}</p>
            <div class="meta">{{ c.fecha.strftime('%d/%m/%Y %H:%M') if c.fecha else '' }}</div>
        </div>
        {% endfor %}

        {% if not comentarios %}
            <p style="color:#888; text-align:center; margin:20px">No hay comentarios aún. ¡Sé el primero!</p>
        {% endif %}

        <div class="info-box" style="margin-top:30px; border-top: 2px solid #7f5af0;">
            <h3>Alumno / Desarrollador</h3>
            <p>Práctica 06 - Desarrollado Exitosamente</p>
        </div>
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    init_db()
    if request.method == "POST":
        nombre = request.form.get("nombre", "")
        campus = request.form.get("campus", "")
        comentario = request.form.get("comentario", "")
        if nombre and comentario:
            guardar_comentario(nombre, campus, comentario)
            return redirect(url_for("index"))
            
    comentarios = obtener_comentarios()
    # Verificación real intentando conectar
    conn_prueba = get_db()
    db_ok = conn_prueba is not None
    if conn_prueba:
        conn_prueba.close()
        
    return render_template_string(TEMPLATE, comentarios=comentarios, db_ok=db_ok)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
