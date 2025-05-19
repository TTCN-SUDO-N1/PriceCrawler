from flask import request
from flask_restx import Namespace, Resource, fields
from NewApp.models import Product
from NewApp import db

api = Namespace('product', description='Product related operations')

product_input_model = api.model('ProductInput', {
    'name': fields.String(required=True, description='Product name'),
    'sku': fields.String(description='SKU'),
    'link': fields.String(description='Product link'),
    'org_price': fields.Float(description='Original price'),
    'cur_price': fields.Float(description='Current price'),
})

product_output_model = api.model('ProductOutput', {
    'id': fields.Integer(readonly=True, description='Product unique identifier'),
    'name': fields.String(required=True, description='Product name'),
    'sku': fields.String(description='SKU'),
    'link': fields.String(description='Product link'),
    'org_price': fields.Float(description='Original price'),
    'cur_price': fields.Float(description='Current price'),
    'created_at': fields.String(description='Created at'),
    'updated_at': fields.String(description='Updated at'),
})

@api.route('/')
class ProductList(Resource):
    @api.doc('list_products', description='Get a list of all products')
    @api.marshal_list_with(product_output_model)
    def get(self):
        return Product.query.all(), 200

    @api.expect(product_input_model)
    @api.marshal_with(product_output_model, code=201)
    @api.doc('create_product', description='Create a new product')
    def post(self):
        data = request.json
        new_product = Product(
            name=data['name'],
            sku=data.get('sku'),
            link=data.get('link'),
            org_price=data.get('org_price'),
            cur_price=data.get('cur_price')
        )
        db.session.add(new_product)
        db.session.commit()
        return new_product, 201

@api.route('/<int:product_id>')
@api.param('product_id', 'Product unique identifier')
@api.response(404, 'Product not found')
class ProductResource(Resource):
    @api.doc('get_product', description='Get a product by its ID')
    @api.marshal_with(product_output_model)
    def get(self, product_id):
        product = Product.query.get_or_404(product_id)
        return product, 200

    @api.expect(product_input_model)
    @api.marshal_with(product_output_model)
    @api.doc('update_product', description='Update a product by its ID')
    def put(self, product_id):
        data = request.json
        product = Product.query.get_or_404(product_id)
        product.name = data['name']
        product.sku = data.get('sku')
        product.link = data.get('link')
        product.org_price = data.get('org_price')
        product.cur_price = data.get('cur_price')
        db.session.commit()
        return product, 200

    @api.doc('delete_product', description='Delete a product by its ID')
    def delete(self, product_id):
        product = Product.query.get_or_404(product_id)
        db.session.delete(product)
        db.session.commit()
        return '', 204
