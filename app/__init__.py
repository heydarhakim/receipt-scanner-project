from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()

def create_app():
    # 1. Initialize Flask with explicit folder paths
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    # 2. Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-123')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///expenses.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'static/uploads')

    # 3. Create Upload Folder if it doesn't exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    CORS(app)
    db.init_app(app)

    with app.app_context():
        # Import parts of our application
        from . import routes, models
        
        # Create Database Tables
        db.create_all()  

        # --- THE MISSING LINK ---
        # We must register the blueprint for the routes to work!
        app.register_blueprint(routes.bp)
        # ------------------------

    return app