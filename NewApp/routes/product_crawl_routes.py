from flask import request
from flask_restx import Namespace, Resource, fields
from NewApp.models import ProductCrawl
from NewApp import db

api = Namespace('product_crawl', description='ProductCrawl related operations')

product_crawl_input_model = api.model('ProductCrawlInput', {
    'prod_id': fields.Integer(required=True, description='Product ID'),
    'enemy_id': fields.Integer(required=True, description='Enemy ID'),
    'link': fields.String(required=True, description='Crawl link'),
})

product_crawl_output_model = api.model('ProductCrawlOutput', {
    'id': fields.Integer(readonly=True, description='ProductCrawl unique identifier'),
    'prod_id': fields.Integer(description='Product ID'),
    'enemy_id': fields.Integer(description='Enemy ID'),
    'link': fields.String(description='Crawl link'),
    'created_at': fields.String(description='Created at'),
    'updated_at': fields.String(description='Updated at'),
})

@api.route('/')
class ProductCrawlList(Resource):
    @api.doc('list_product_crawls', description='Get a list of all product crawls')
    @api.marshal_list_with(product_crawl_output_model)
    def get(self):
        return ProductCrawl.query.all(), 200

    @api.expect(product_crawl_input_model)
    @api.marshal_with(product_crawl_output_model, code=201)
    @api.doc('create_product_crawl', description='Create a new product crawl')
    def post(self):
        data = request.json
        new_crawl = ProductCrawl(
            prod_id=data['prod_id'],
            enemy_id=data['enemy_id'],
            link=data['link']
        )
        db.session.add(new_crawl)
        db.session.commit()
        return new_crawl, 201

@api.route('/<int:crawl_id>')
@api.param('crawl_id', 'ProductCrawl unique identifier')
@api.response(404, 'ProductCrawl not found')
class ProductCrawlResource(Resource):
    @api.doc('get_product_crawl', description='Get a product crawl by its ID')
    @api.marshal_with(product_crawl_output_model)
    def get(self, crawl_id):
        crawl = ProductCrawl.query.get_or_404(crawl_id)
        return crawl, 200

    @api.expect(product_crawl_input_model)
    @api.marshal_with(product_crawl_output_model)
    @api.doc('update_product_crawl', description='Update a product crawl by its ID')
    def put(self, crawl_id):
        data = request.json
        crawl = ProductCrawl.query.get_or_404(crawl_id)
        crawl.prod_id = data['prod_id']
        crawl.enemy_id = data['enemy_id']
        crawl.link = data['link']
        db.session.commit()
        return crawl, 200

    @api.doc('delete_product_crawl', description='Delete a product crawl by its ID')
    def delete(self, crawl_id):
        crawl = ProductCrawl.query.get_or_404(crawl_id)
        db.session.delete(crawl)
        db.session.commit()
        return '', 204
