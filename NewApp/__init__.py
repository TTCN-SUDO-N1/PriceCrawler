from NewApp.config import Config
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_restx import Api
from flask_migrate import Migrate


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
    api.init_app(app)
    from NewApp.routes.enemy_routes import api as enemy_ns
    from NewApp.routes.product_routes import api as product_ns
    from NewApp.routes.product_crawl_routes import api as product_crawl_ns
    from NewApp.routes.product_crawl_log_routes import api as product_crawl_log_ns
    from NewApp.index import ns as index_ns

    api.add_namespace(enemy_ns, path='/api/enemies')
    api.add_namespace(product_ns, path='/api/product')
    api.add_namespace(product_crawl_ns, path='/api/product-crawls')
    api.add_namespace(product_crawl_log_ns, path='/api/product-crawl-logs')
    api.add_namespace(index_ns, path='/index')
    
    with app.app_context():
        db.create_all()
        
    return app