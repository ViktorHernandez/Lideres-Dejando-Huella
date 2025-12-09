from flask import Flask, jsonify, request  
from flask_cors import CORS
from config import UPLOAD_FOLDER, APP_HOST, APP_PORT
from database import close_db
import os
import logging 
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from wtforms import Form, StringField, PasswordField, validators  

logging.basicConfig(
    filename='api.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s' 
)

from routes.users import users_bp
from routes.animals import animals_bp
from routes.media import media_bp
from routes.contact import contact_bp
from routes.social import social_bp
from routes.adoptions import adoptions_bp
from routes.comments import comments_bp

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
CORS(app, resources={r"/api/*": {"origins": "*"}})

limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)

app.teardown_appcontext(close_db)

app.register_blueprint(users_bp)
app.register_blueprint(animals_bp)
app.register_blueprint(media_bp)
app.register_blueprint(contact_bp)
app.register_blueprint(social_bp)
app.register_blueprint(adoptions_bp)
app.register_blueprint(comments_bp)

class UserForm(Form):
    name = StringField('name', [validators.Length(min=1, max=100), validators.DataRequired()])
    email = StringField('email', [validators.Email(), validators.DataRequired()])
    password = PasswordField('password', [validators.Length(min=6), validators.DataRequired()])

@app.errorhandler(500)
def internal_error(error):
    logging.error(f"Error interno del servidor: {str(error)}")
    return jsonify({"error": "Error interno del servidor. Inténtalo de nuevo más tarde."}), 500

@app.errorhandler(404)
def not_found(error):
    logging.warning(f"Ruta no encontrada: {request.url}") 
    return jsonify({"error": "Recurso no encontrado"}), 404

@app.errorhandler(400)
def bad_request(error):
    logging.warning(f"Solicitud mala: {str(error)}")
    return jsonify({"error": "Solicitud inválida"}), 400

@app.errorhandler(401)
def unauthorized(error):
    logging.warning(f"Acceso no autorizado: {request.url}")
    return jsonify({"error": "No autorizado"}), 401

@app.route("/", methods=["GET"])
@limiter.limit("10 per minute")
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