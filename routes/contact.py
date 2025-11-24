from flask import Blueprint, request, jsonify, g
from database import get_db
from auth import token_required

contact_bp = Blueprint('contact', __name__, url_prefix='/api/v1')

@contact_bp.route("/contact", methods=["GET"])
def get_contact():
    db = get_db()
    cur = db.execute("SELECT * FROM shelter_contact WHERE id=1")
    row = cur.fetchone()
    return jsonify(dict(row)) if row else jsonify({"message": "Aún sin datos"})

@contact_bp.route("/contact", methods=["POST"])
@token_required
def set_contact():
    if g.current_user["role"] != "admin":
        return jsonify({"error": "Sólo administradores pueden actualizar contacto"}), 403
    data = request.get_json(force=True) or {}
    email = data.get("email")
    phone = data.get("phone")
    address = data.get("address")
    db = get_db()
    db.execute("DELETE FROM shelter_contact WHERE id=1")
    db.execute("INSERT INTO shelter_contact (id, email, phone, address) VALUES (1, ?, ?, ?)",
               (email, phone, address))
    db.commit()
    return jsonify({"message": "Contacto actualizado"})