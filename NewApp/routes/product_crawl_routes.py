from flask import request
from flask_restx import Namespace, Resource, fields
from NewApp import db
from NewApp.models import ProductCrawl
from OCR.screenshot import scrape
from NewApp.models import ProductCrawlLog

api = Namespace('product_crawl', description='ProductCrawl related operations')

product_crawl_input_model = api.model('ProductCrawlInput', {
    'prod_id': fields.Integer(required=True, description='Product ID'),
    'enemy_id': fields.Integer(required=True, description='Enemy ID'),
    'link': fields.String(required=True, description='Crawl link'),
})

product_crawl_link_input_model = api.model('ProductCrawlLinkInput', {
    'link': fields.String(required=True, description='Crawl link'),
})
product_crawl_output_model = api.model('ProductCrawlOutput', {
    'id': fields.Integer(readonly=True, description='ProductCrawl unique identifier'),
    'prod_id': fields.Integer(description='Product ID'),
    'enemy_id': fields.Integer(description='Enemy ID'),
    'link': fields.String(description='Crawl link'),
    'created_at': fields.String(description='Created at'),
    'updated_at': fields.String(description='Updated at'),
    'logs': fields.List(fields.Nested(api.model('ProductCrawlLog', {
        'id': fields.Integer(readonly=True, description='Log unique identifier'),
        'product_crawl_id': fields.Integer(description='ProductCrawl ID'),
        'name': fields.String(description='Log name'),
        'price': fields.Float(description='Price'),
        'timestamp': fields.String(description='Timestamp'),
        'other_data': fields.Raw(description='Other data'),
    })))
})

@api.route('/')
class ProductCrawlList(Resource):
    @api.doc('list_product_crawls', description='Get a list of all product crawls')
    @api.param('prod_id', 'Filter by product ID')
    @api.marshal_list_with(product_crawl_output_model)
    def get(self):
        prod_id = request.args.get('prod_id')
        if prod_id:
            crawls = ProductCrawl.query.filter_by(prod_id=prod_id).all()
            if not crawls and prod_id:
                api.abort(404, f"No enemy products found for product ID: {prod_id}")
            return crawls, 200
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

@api.route('/by-link')
class ProductCrawlByLink(Resource):
    """Resource for retrieving Enemy ProductCrawl (enemy product) by link."""

    @api.doc('get_product_crawl_by_link', description='Get enemy product crawl info by link')
    @api.param('link', 'Crawl link', required=True)
    @api.marshal_with(product_crawl_output_model)
    def get(self):
        # Get link from query string, not request.json
        link = request.args.get('link')
        if not link:
            api.abort(400, 'Missing required parameter: link')
        crawl = ProductCrawl.query.filter_by(link=link).first()
        if not crawl:
            api.abort(404, 'ProductCrawl (enemy product) not found')
        return crawl, 200

@api.route('/crawl-link')
class CrawlByLink(Resource):

    @api.doc('crawl_by_link', description='Crawl a product by link, save log, and return crawl info')
    @api.expect(api.model('CrawlRequest', {
        'link': fields.String(required=False, description='Crawl link'),
        'crawl_id': fields.Integer(required=False, description='Product Crawl ID')
    }))
    @api.marshal_with(product_crawl_output_model)
    def post(self):
        data = request.json
        link = data.get('link')
        crawl_id = data.get('crawl_id')
        
        # Check if we have either link or crawl_id
        if not link and not crawl_id:
            api.abort(400, 'Missing required parameter: either link or crawl_id must be provided')
            
        # Get crawl object
        crawl = None
        if crawl_id:
            crawl = ProductCrawl.query.get_or_404(crawl_id)
            link = crawl.link
        elif link:
            crawl = ProductCrawl.query.filter_by(link=link).first()
            if not crawl:
                api.abort(404, 'ProductCrawl (enemy product) not found for this link')
                
        # Call the scrape function
        try:
            crawl_result = scrape(link)
            
            # Save log
            log = ProductCrawlLog(
                product_crawl_id=crawl.id,
                name=crawl_result.get('product_name', 'Unknown'),
                price=crawl_result.get('current_price'),
                other_data=crawl_result,
            )
            db.session.add(log)
            db.session.commit()
            return crawl, 200
        except Exception as e:
            api.abort(500, f'Error crawling the product: {str(e)}')
            
        return crawl, 200

