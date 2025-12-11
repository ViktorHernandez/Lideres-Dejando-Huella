import os

DB_PATH = os.path.join(os.path.dirname(__file__), "adopcion.db")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "mp4", "webm", "mov"}
APP_HOST = "0.0.0.0"
APP_PORT = int(os.environ.get("PORT", 5000))
TOKEN_EXPIRY_DAYS = 7
