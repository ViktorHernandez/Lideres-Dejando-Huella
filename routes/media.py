from flask import Blueprint, request, jsonify, g, send_from_directory
from werkzeug.utils import secure_filename
import os
import secrets
import subprocess
from PIL import Image
import cv2
import time
from database import get_db
from auth import token_required
from utils import allowed_file
from config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS

media_bp = Blueprint('media', __name__, url_prefix='/api/v1')

MAX_IMAGE_SIZE = 3 * 1024 * 1024
MAX_VIDEO_SIZE = 20 * 1024 * 1024
THUMBNAIL_SIZE = (300, 300)
MAX_WIDTH = 1920
MAX_HEIGHT = 1080
RATE_LIMIT_SECONDS = 5
LAST_UPLOAD = {}

def scan_with_clamav(path):
    try:
        result = subprocess.run(
            ["clamscan", path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return "Infected files: 0" in result.stdout
    except Exception:
        return True

def compress_image(path):
    try:
        img = Image.open(path)
        img.save(path, optimize=True, quality=70)
    except Exception:
        pass

def resize_image(path):
    try:
        img = Image.open(path)
        img.thumbnail((MAX_WIDTH, MAX_HEIGHT))
        img.save(path)
    except Exception:
        pass

def create_thumbnail(path, thumb_path):
    try:
        img = Image.open(path)
        img.thumbnail(THUMBNAIL_SIZE)
        img.save(thumb_path)
    except Exception:
        pass

def get_video_duration(path):
    try:
        video = cv2.VideoCapture(path)
        frames = video.get(cv2.CAP_PROP_FRAME_COUNT)
        fps = video.get(cv2.CAP_PROP_FPS)
        if fps == 0:
            return 0
        return frames / fps
    except Exception:
        return 0

@media_bp.route("/media/upload", methods=["POST"])
@token_required
def upload_media():
    user_id = g.current_user["id"]

    if user_id in LAST_UPLOAD and time.time() - LAST_UPLOAD[user_id] < RATE_LIMIT_SECONDS:
        return jsonify({"error": "Espera unos segundos antes de subir otro archivo"}), 429

    if "file" not in request.files:
        return jsonify({"error": "Falta archivo 'file'"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Nombre de archivo vacío"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": f"Tipo de archivo no permitido. Permitidos: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)

    extension = file.filename.rsplit(".", 1)[1].lower()

    if extension in {"png", "jpg", "jpeg", "gif"}:
        if size > MAX_IMAGE_SIZE:
            return jsonify({"error": "La imagen excede el límite de 3MB"}), 400
    else:
        if size > MAX_VIDEO_SIZE:
            return jsonify({"error": "El video excede el límite de 20MB"}), 400

    filename = secure_filename(f"{secrets.token_hex(8)}_{file.filename}")
    saved_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(saved_path)

    if not scan_with_clamav(saved_path):
        os.remove(saved_path)
        return jsonify({"error": "El archivo fue rechazado por contener malware"}), 400

    if extension in {"png", "jpg", "jpeg"}:
        resize_image(saved_path)
        compress_image(saved_path)
        thumbnail_name = f"thumb_{filename}"
        thumb_path = os.path.join(UPLOAD_FOLDER, thumbnail_name)
        create_thumbnail(saved_path, thumb_path)
    else:
        duration = get_video_duration(saved_path)
        if duration == 0:
            os.remove(saved_path)
            return jsonify({"error": "No se pudo validar el video"}), 400

    animal_id = request.form.get("animal_id")
    title = request.form.get("title")
    description = request.form.get("description")

    media_type = "image" if extension in {"png", "jpg", "jpeg", "gif"} else "video"

    db = get_db()

    if animal_id:
        cur = db.execute("SELECT id FROM animals WHERE id = ?", (animal_id,))
        if not cur.fetchone():
            return jsonify({"error": "Animal no encontrado"}), 404
        db.execute(
            "INSERT INTO animal_media (animal_id, media_type, file_path, title, description) VALUES (?, ?, ?, ?, ?)",
            (animal_id, media_type, f"/uploads/{filename}", title, description)
        )
    else:
        db.execute(
            "INSERT INTO animal_media (animal_id, media_type, file_path, title, description) VALUES (0, ?, ?, ?, ?)",
            (media_type, f"/uploads/{filename}", title, description)
        )

    db.commit()

    LAST_UPLOAD[user_id] = time.time()

    return jsonify({
        "file_path": f"/uploads/{filename}",
        "title": title,
        "description": description
    }), 201

@media_bp.route("/uploads/<path:filename>", methods=["GET"])
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)