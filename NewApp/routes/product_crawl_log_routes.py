from flask import request
from flask_restx import Namespace, Resource, fields
from NewApp import db
from NewApp.models import ProductCrawlLog

api = Namespace('product_crawl_log', description='ProductCrawlLog related operations')

product_crawl_log_input_model = api.model('ProductCrawlLogInput', {
    'product_crawl_id': fields.Integer(required=True, description='ProductCrawl ID'),
    'name': fields.String(required=True, description='Log name'),
    'price': fields.Float(description='Price'),
    'other_data': fields.Raw(description='Other data'),
})

product_crawl_log_output_model = api.model('ProductCrawlLogOutput', {
    'id': fields.Integer(readonly=True, description='Log unique identifier'),
    'product_crawl_id': fields.Integer(description='ProductCrawl ID'),
    'name': fields.String(description='Log name'),
    'price': fields.Float(description='Price'),
    'timestamp': fields.String(description='Timestamp'),
    'other_data': fields.Raw(description='Other data'),
})

@api.route('/')
class ProductCrawlLogList(Resource):
    @api.doc('list_product_crawl_logs', description='Get a list of all product crawl logs')
    @api.marshal_list_with(product_crawl_log_output_model)
    def get(self):
        return ProductCrawlLog.query.all(), 200

    @api.expect(product_crawl_log_input_model)
    @api.marshal_with(product_crawl_log_output_model, code=201)
    @api.doc('create_product_crawl_log', description='Create a new product crawl log')
    def post(self):
        data = request.json
        new_log = ProductCrawlLog(
            product_crawl_id=data['product_crawl_id'],
            name=data['name'],
            price=data.get('price'),
            other_data=data.get('other_data')
        )
        db.session.add(new_log)
        db.session.commit()
        return new_log, 201

@api.route('/<int:log_id>')
@api.param('log_id', 'Log unique identifier')
@api.response(404, 'Log not found')
class ProductCrawlLogResource(Resource):
    @api.doc('get_product_crawl_log', description='Get a product crawl log by its ID')
    @api.marshal_with(product_crawl_log_output_model)
    def get(self, log_id):
        log = ProductCrawlLog.query.get_or_404(log_id)
        return log, 200

    @api.expect(product_crawl_log_input_model)
    @api.marshal_with(product_crawl_log_output_model)
    @api.doc('update_product_crawl_log', description='Update a product crawl log by its ID')
    def put(self, log_id):
        data = request.json
        log = ProductCrawlLog.query.get_or_404(log_id)
        log.product_crawl_id = data['product_crawl_id']
        log.name = data['name']
        log.price = data.get('price')
        log.other_data = data.get('other_data')
        db.session.commit()
        return log, 200

    @api.doc('delete_product_crawl_log', description='Delete a product crawl log by its ID')
    def delete(self, log_id):
        log = ProductCrawlLog.query.get_or_404(log_id)
        db.session.delete(log)
        db.session.commit()
        return '', 204
