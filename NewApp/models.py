from NewApp import db
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import DeclarativeMeta
import json


class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    sku = db.Column(db.String(100))
    link = db.Column(db.Text)
    org_price = db.Column(db.Numeric(12, 2))
    cur_price = db.Column(db.Numeric(12, 2))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    product_crawls = relationship("ProductCrawl", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Product {self.name}>"
        
    def to_dict(self, include_relationships=True):
        result = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        # Convert Decimal to float for JSON serialization
        if 'org_price' in result and result['org_price'] is not None:
            result['org_price'] = float(result['org_price'])
        if 'cur_price' in result and result['cur_price'] is not None:
            result['cur_price'] = float(result['cur_price'])
        # Convert datetime objects to ISO format
        if 'created_at' in result and result['created_at'] is not None:
            result['created_at'] = result['created_at'].isoformat()
        if 'updated_at' in result and result['updated_at'] is not None:
            result['updated_at'] = result['updated_at'].isoformat()
        
        if include_relationships:
            result['product_crawls'] = [pc.to_dict(include_relationships=False) for pc in self.product_crawls]
        
        return result


class Enemy(db.Model):
    __tablename__ = 'enemies'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    domain = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    product_crawls = relationship("ProductCrawl", back_populates="enemy", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Enemy {self.name}>"
    
    def to_dict(self, include_relationships=True):
        result = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        # Convert datetime objects to ISO format
        if 'created_at' in result and result['created_at'] is not None:
            result['created_at'] = result['created_at'].isoformat()
        if 'updated_at' in result and result['updated_at'] is not None:
            result['updated_at'] = result['updated_at'].isoformat()
        
        if include_relationships:
            result['product_crawls'] = [pc.to_dict(include_relationships=False) for pc in self.product_crawls]
        
        return result


class ProductCrawl(db.Model):
    __tablename__ = 'product_crawls'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prod_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    enemy_id = db.Column(db.Integer, db.ForeignKey('enemies.id', ondelete='CASCADE'), nullable=False)
    link = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="product_crawls")
    enemy = relationship("Enemy", back_populates="product_crawls")
    logs = relationship("ProductCrawlLog", back_populates="product_crawl", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ProductCrawl {self.id}>"
    
    def to_dict(self, include_relationships=True):
        result = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        # Convert datetime objects to ISO format
        if 'created_at' in result and result['created_at'] is not None:
            result['created_at'] = result['created_at'].isoformat()
        if 'updated_at' in result and result['updated_at'] is not None:
            result['updated_at'] = result['updated_at'].isoformat()
        
        if include_relationships:
            # Include basic product and enemy info without their relationships
            if self.product:
                result['product'] = {
                    'id': self.product.id,
                    'name': self.product.name,
                    'sku': self.product.sku
                }
            if self.enemy:
                result['enemy'] = {
                    'id': self.enemy.id,
                    'name': self.enemy.name,
                    'domain': self.enemy.domain
                }
            result['logs'] = [log.to_dict(include_relationships=False) for log in self.logs]
        
        return result


class ProductCrawlLog(db.Model):
    __tablename__ = 'product_crawl_logs'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_crawl_id = db.Column(db.Integer, db.ForeignKey('product_crawls.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Numeric(12, 2))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    other_data = db.Column(db.JSON)
    
    # Relationships
    product_crawl = relationship("ProductCrawl", back_populates="logs")
    
    def __repr__(self):
        return f"<ProductCrawlLog {self.id}>"
    
    def to_dict(self, include_relationships=True):
        result = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        # Convert Decimal to float for JSON serialization
        if 'price' in result and result['price'] is not None:
            result['price'] = float(result['price'])
        # Convert datetime objects to ISO format
        if 'timestamp' in result and result['timestamp'] is not None:
            result['timestamp'] = result['timestamp'].isoformat()
        
        if include_relationships and self.product_crawl:
            result['product_crawl'] = {
                'id': self.product_crawl.id,
                'prod_id': self.product_crawl.prod_id,
                'enemy_id': self.product_crawl.enemy_id,
                'link': self.product_crawl.link
            }
        
        return result