import secrets
import datetime
from functools import wraps
from flask import request, jsonify, g
from database import get_db
import bcrypt


def generate_token():
    return secrets.token_urlsafe(32)


def hash_password(password):
    """Función para hashear una contraseña usando bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())


def check_password(password, hashed):
    """Función para verificar una contraseña contra su hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed)


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Se requiere token de autorización"}), 401

        token = auth.split(" ", 1)[1].strip()

        db = get_db()
        cur = db.execute(
            "SELECT token, user_id, expires_at FROM tokens WHERE token = ?",
            (token,)
        )
        row = cur.fetchone()

        if not row:
            return jsonify({"error": "Token inválido"}), 401

        expires_at = datetime.datetime.fromisoformat(row["expires_at"])
        if datetime.datetime.utcnow() > expires_at:
            db.execute("DELETE FROM tokens WHERE token = ?", (token,))
            db.commit()
            return jsonify({"error": "Token expirado"}), 401

        cur = db.execute(
            "SELECT id, name, email, role FROM users WHERE id = ?",
            (row["user_id"],)
        )
        user = cur.fetchone()

        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 401

        g.current_user = user
        g.current_token = token

        return f(*args, **kwargs)

    return decorated