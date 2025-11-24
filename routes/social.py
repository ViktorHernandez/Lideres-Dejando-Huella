from flask import Blueprint, request, jsonify, g
from database import get_db
from auth import token_required

social_bp = Blueprint('social', __name__, url_prefix='/api/v1')

@social_bp.route("/social", methods=["GET"])
def get_social():
    db = get_db()
    cur = db.execute("SELECT * FROM shelter_social WHERE id=1")
    row = cur.fetchone()
    return jsonify(dict(row)) if row else jsonify({"message": "Aún sin datos"})

@social_bp.route("/social", methods=["POST"])
@token_required
def set_social():
    if g.current_user["role"] != "admin":
        return jsonify({"error": "Sólo administradores pueden actualizar redes sociales"}), 403
    data = request.get_json(force=True) or {}
    facebook = data.get("facebook")
    instagram = data.get("instagram")
    tiktok = data.get("tiktok")
    youtube = data.get("youtube")
    db = get_db()
    db.execute("DELETE FROM shelter_social WHERE id=1")
    db.execute("INSERT INTO shelter_social (id, facebook, instagram, tiktok, youtube) VALUES (1, ?, ?, ?, ?)",
               (facebook, instagram, tiktok, youtube))
    db.commit()
    return jsonify({"message": "Redes sociales actualizadas"})