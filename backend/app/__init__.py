from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv
import os

db = SQLAlchemy()
migrate = Migrate()

# Import the model at the top level
from app.models import GroupedDailyBars, GapData

def create_app():
    load_dotenv()  # Load environment variables from .env file

    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smallcapgaps.db' 
    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        # Import your models here to avoid circular imports
        from app.models import GroupedDailyBars, GapData
        from app.routes import api_bp
        app.register_blueprint(api_bp, url_prefix='/api')

    return app