from flask import Blueprint, request, jsonify, g, send_from_directory
from werkzeug.utils import secure_filename
import os
import secrets
from database import get_db
from auth import token_required
from utils import allowed_file
from config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS

media_bp = Blueprint('media', __name__, url_prefix='/api/v1')

@media_bp.route("/media/upload", methods=["POST"])
@token_required
def upload_media():
    if "file" not in request.files:
        return jsonify({"error": "Falta archivo 'file'"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Nombre de archivo vacío"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": f"Tipo de archivo no permitido. Permitidos: {', '.join(ALLOWED_EXTENSIONS)}"}), 400
    filename = secure_filename(f"{secrets.token_hex(8)}_{file.filename}")
    saved_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(saved_path)
    animal_id = request.form.get("animal_id")
    title = request.form.get("title")
    description = request.form.get("description")
    media_type = "image" if filename.rsplit(".", 1)[1].lower() in {"png", "jpg", "jpeg", "gif"} else "video"
    db = get_db()
    if animal_id:
        cur = db.execute("SELECT id FROM animals WHERE id = ?", (animal_id,))
        if not cur.fetchone():
            return jsonify({"error": "Animal no encontrado"}), 404
        db.execute("INSERT INTO animal_media (animal_id, media_type, file_path, title, description) VALUES (?, ?, ?, ?, ?)",
                   (animal_id, media_type, f"/uploads/{filename}", title, description))
    else:
        db.execute("INSERT INTO animal_media (animal_id, media_type, file_path, title, description) VALUES (0, ?, ?, ?, ?)",
                   (media_type, f"/uploads/{filename}", title, description))
    db.commit()
    return jsonify({"file_path": f"/uploads/{filename}", "title": title, "description": description}), 201

@media_bp.route("/uploads/<path:filename>", methods=["GET"])
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)