from flask import Blueprint, request, jsonify, g
from database import get_db
from auth import token_required, generate_token
import datetime
from config import TOKEN_EXPIRY_DAYS

users_bp = Blueprint('users', __name__, url_prefix='/api/v1')

@users_bp.route("/users", methods=["POST"])
def create_user():
    data = request.get_json(force=True) or {}
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "user")
    if role not in ("user", "admin"):
        role = "user"
    if not all([name, email, password]):
        return jsonify({"error": "name, email y password obligatorios"}), 400
    db = get_db()
    try:
        cur = db.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                         (name, email, password, role))
        db.commit()
        return jsonify({"id": cur.lastrowid, "name": name, "email": email, "role": role}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "email ya registrado"}), 400

@users_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True) or {}
    email = data.get("email")
    password = data.get("password")
    if not all([email, password]):
        return jsonify({"error": "email y password requeridos"}), 400
    db = get_db()
    cur = db.execute("SELECT id, name, email, role FROM users WHERE email = ? AND password = ?", (email, password))
    row = cur.fetchone()
    if not row:
        return jsonify({"success": False, "message": "Credenciales incorrectas"}), 401
    token = generate_token()
    expires_at = (datetime.datetime.utcnow() + datetime.timedelta(days=TOKEN_EXPIRY_DAYS)).isoformat()
    db.execute("INSERT INTO tokens (token, user_id, expires_at) VALUES (?, ?, ?)", (token, row["id"], expires_at))
    db.commit()
    return jsonify({
        "success": True,
        "message": f"Sesión iniciada como: {row['name']} ({row['email']})",
        "user": {"id": row["id"], "name": row["name"], "email": row["email"], "role": row["role"]},
        "token": token,
        "expires_at": expires_at
    })

@users_bp.route("/logout", methods=["POST"])
@token_required
def logout():
    db = get_db()
    db.execute("DELETE FROM tokens WHERE token = ?", (g.current_token,))
    db.commit()
    return jsonify({"message": "Sesión cerrada"})

@users_bp.route("/profile", methods=["GET"])
@token_required
def get_profile():
    db = get_db()
    cur = db.execute("SELECT u.id, u.name, u.email, u.role, ap.phone, ap.address, ap.about, ap.created_at as profile_created_at FROM users u LEFT JOIN adopter_profiles ap ON u.id = ap.user_id WHERE u.id = ?", (g.current_user["id"],))
    row = cur.fetchone()
    return jsonify(dict(row)) if row else jsonify({"error": "Perfil no encontrado"}), 404

@users_bp.route("/profile", methods=["POST", "PUT"])
@token_required
def set_profile():
    data = request.get_json(force=True) or {}
    phone = data.get("phone")
    address = data.get("address")
    about = data.get("about")
    db = get_db()
    cur = db.execute("SELECT user_id FROM adopter_profiles WHERE user_id = ?", (g.current_user["id"],))
    if cur.fetchone():
        db.execute("UPDATE adopter_profiles SET phone = ?, address = ?, about = ? WHERE user_id = ?",
                   (phone, address, about, g.current_user["id"]))
    else:
        db.execute("INSERT INTO adopter_profiles (user_id, phone, address, about) VALUES (?, ?, ?, ?)",
                   (g.current_user["id"], phone, address, about))
    db.commit()
    cur = db.execute("SELECT u.id, u.name, u.email, u.role, ap.phone, ap.address, ap.about, ap.created_at as profile_created_at FROM users u LEFT JOIN adopter_profiles ap ON u.id = ap.user_id WHERE u.id = ?", (g.current_user["id"],))
    return jsonify(dict(cur.fetchone()))