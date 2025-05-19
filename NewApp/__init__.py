from NewApp.config import Config
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_restx import Api
from flask_migrate import Migrate

from routes.enemy_routes import api as enemy_ns
from routes.product_routes import api as product_ns
from routes.product_crawl_routes import api as product_crawl_ns
from routes.product_crawl_log_routes import api as product_crawl_log_ns

def register_api(app):
    api = Api(app, version='1.0', title='Product Crawler API',
              description='API for managing products, enemies, crawls, and logs')
    api.add_namespace(enemy_ns, path='/enemies')
    api.add_namespace(product_ns, path='/products')
    api.add_namespace(product_crawl_ns, path='/product-crawls')
    api.add_namespace(product_crawl_log_ns, path='/product-crawl-logs')
    return api
    
migrate = Migrate()
api = Api(
    doc='/api/'
)
db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    register_api(app)
    
    with app.app_context():
        db.create_all()
        
    return app