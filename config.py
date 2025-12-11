import os

DB_PATH = os.path.join(os.path.dirname(__file__), "adopcion.db")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "mp4", "webm", "mov"}
APP_HOST = "127.0.0.1"
APP_PORT = 5000
TOKEN_EXPIRY_DAYS = 7