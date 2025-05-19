from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
# from flask_restx import Api
from NewApp.config import Config
# from flask_mail import Mail
from flask_migrate import Migrate

migrate = Migrate()
db =SQLAlchemy()

def create_app():
    app=Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    with app.app_context():
        db.create_all()
        
    return app