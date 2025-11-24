from flask import Flask, jsonify
from flask_cors import CORS
from config import UPLOAD_FOLDER, APP_HOST, APP_PORT
from database import close_db
import os

# Importar blueprints
from routes.users import users_bp
from routes.animals import animals_bp
from routes.media import media_bp
from routes.contact import contact_bp
from routes.social import social_bp
from routes.adoptions import adoptions_bp
from routes.comments import comments_bp

# Crear la app
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Registrar teardown
app.teardown_appcontext(close_db)

# Registrar blueprints
app.register_blueprint(users_bp)
app.register_blueprint(animals_bp)
app.register_blueprint(media_bp)
app.register_blueprint(contact_bp)
app.register_blueprint(social_bp)
app.register_blueprint(adoptions_bp)
app.register_blueprint(comments_bp)

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "API de adopción funcionando",
        "version": "v1",
        "api_base": "/api/v1/",
        "endpoints": [
            "/api/v1/users (POST)",
            "/api/v1/login (POST)",
            "/api/v1/animals (GET,POST)",
            "/api/v1/animals/<id> (GET,PUT,DELETE)",
            "/api/v1/animals/<id>/media (GET)",
            "/api/v1/media/upload (POST multipart/form-data)",
            "/api/v1/contact (GET,POST)",
            "/api/v1/social (GET,POST)",
            "/api/v1/adoptions (GET,POST,PUT status by admin)",
            "/api/v1/comments (GET,POST,DELETE)",
            "/api/v1/profile (GET,POST,PUT)"
        ]
    })