from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER')

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    CORS(app)
    db.init_app(app)

    with app.app_context():
        from . import routes, models
        db.create_all()  # Create SQLite tables

    return app