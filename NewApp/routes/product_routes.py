from flask import request
from flask_restx import Namespace, Resource, fields
from NewApp import db
from NewApp.models import Product
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../OCR')))
from OCR.screenshot import scrape,process_urls_in_batches

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

product_info_input_model = api.model('ProductInfoInput', {
    'link': fields.String(required=True, description='Product link'),
})
product_info_output_model = api.model('ProductInfoOutput', {
    'name': fields.String(description='Product name'),
    'sku': fields.String(description='SKU'),
    'org_price': fields.Float(description='Original price'),
    'cur_price': fields.Float(description='Current price'),
})

pagination_model = api.model('Pagination', {
    'page': fields.Integer(description='Current page number'),
    'per_page': fields.Integer(description='Items per page'),
    'total': fields.Integer(description='Total number of items'),
    'pages': fields.Integer(description='Total number of pages'),
    'has_prev': fields.Boolean(description='Has previous page'),
    'has_next': fields.Boolean(description='Has next page'),
})

product_list_output_model = api.model('ProductListOutput', {
    'products': fields.List(fields.Nested(product_output_model), description='List of products'),
    'pagination': fields.Nested(pagination_model, description='Pagination information'),
})

@api.route('/')
class ProductList(Resource):
    @api.doc('list_products', description='Get a list of all products with search and pagination')
    @api.param('search', 'Search products by name or SKU', _in='query')
    @api.param('page', 'Page number (default: 1)', _in='query')
    @api.param('per_page', 'Items per page (default: 10, max: 100)', _in='query')
    @api.marshal_with(product_list_output_model)
    def get(self):
        search = request.args.get('search', '').strip()
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 100)  # Max 100 items per page
        
        # Build query with search filter
        query = Product.query
        if search:
            search_filter = f'%{search}%'
            query = query.filter(
                (Product.name.ilike(search_filter)) | 
                (Product.sku.ilike(search_filter))
            )
        
        # Apply pagination
        paginated = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Return products with pagination metadata
        result = {
            'products': paginated.items,
            'pagination': {
                'page': paginated.page,
                'per_page': paginated.per_page,
                'total': paginated.total,
                'pages': paginated.pages,
                'has_prev': paginated.has_prev,
                'has_next': paginated.has_next
            }
        }
        
        return result, 200

    @api.expect(product_input_model)
    @api.marshal_with(product_output_model, code=201)
    @api.doc('create_product', description='Create a new product')
    def post(self):
        data = request.json
        try:
            # Safely convert prices to float or None if invalid
            org_price = data.get('org_price')
            cur_price = data.get('cur_price')
            
            # Convert empty strings to None
            if org_price == '':
                org_price = None
            if cur_price == '':
                cur_price = None
                
            # Try to convert to float if not None
            if org_price is not None:
                try:
                    org_price = float(org_price)
                except (ValueError, TypeError):
                    org_price = None
                    
            if cur_price is not None:
                try:
                    cur_price = float(cur_price)
                except (ValueError, TypeError):
                    cur_price = None
            
            new_product = Product(
                name=data['name'],
                sku=data.get('sku'),
                link=data.get('link'),
                org_price=org_price,
                cur_price=cur_price
            )
            db.session.add(new_product)
            db.session.commit()
            return new_product, 201
        except Exception as e:
            db.session.rollback()
            api.abort(400, f"Error creating product: {str(e)}")

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
        
        # Handle org_price - convert empty strings to None
        org_price = data.get('org_price')
        if org_price == '':
            org_price = None
        if org_price is not None:
            try:
                org_price = float(org_price)
            except (ValueError, TypeError):
                org_price = None
        product.org_price = org_price
        
        # Handle cur_price - convert empty strings to None
        cur_price = data.get('cur_price')
        if cur_price == '':
            cur_price = None
        if cur_price is not None:
            try:
                cur_price = float(cur_price)
            except (ValueError, TypeError):
                cur_price = None
        product.cur_price = cur_price
        
        db.session.commit()
        return product, 200

    @api.doc('delete_product', description='Delete a product by its ID')
    def delete(self, product_id):
        product = Product.query.get_or_404(product_id)
        db.session.delete(product)
        db.session.commit()
        return '', 204

@api.route('/extract-info')
class ProductInfo(Resource):
    @api.expect(product_info_input_model)
    @api.marshal_with(product_info_output_model)
    @api.doc('extract_product_info', description='Extract product information from a link')
    def post(self):
        try:
            data = request.json
            link = data['link']
            product_info = scrape(link)
            if not product_info:
                return {'message': 'Failed to extract product information'}, 400
            
            name = product_info.get('product_name')
            sku = product_info.get('sku')
            
            # Get prices and ensure they are valid floats or None
            org_price = product_info.get('promotional_price')
            if org_price == "" or org_price == 0 or org_price is None:
                org_price = None
            
            cur_price = product_info.get('current_price')
            if cur_price == "" or cur_price == 0 or cur_price is None:
                cur_price = None
                
            return {
                'name': name,
                'sku': sku,
                'org_price': org_price,
                'cur_price': cur_price
            }, 200
        except Exception as e:
            api.abort(500, f'Error extracting product info: {str(e)}')

@api.route('/<int:product_id>/crawl')
@api.param('product_id', 'Product unique identifier')
@api.response(404, 'Product not found')
class ProductCrawl(Resource):
    @api.doc('crawl_product', description='Crawl product information by its ID')
    @api.marshal_with(product_output_model)
    def post(self, product_id):
        # Get product
        product = Product.query.get_or_404(product_id)
        
        # Check if product has a link
        if not product.link:
            api.abort(400, 'Product does not have a link to crawl')
            
        try:
            # Crawl product information
            product_info = scrape(product.link)
            
            if not product_info:
                api.abort(500, 'Failed to extract product information')
                
            # Update product information
            if product_info.get('product_name'):
                product.name = product_info.get('product_name')
            
            # Update prices, handling None and zero values properly
            cur_price = product_info.get('current_price')
            if cur_price is not None and cur_price != 0:
                product.cur_price = cur_price
            
            org_price = product_info.get('promotional_price')
            if org_price is not None and org_price != 0:
                product.org_price = org_price
                
            db.session.commit()
            return product, 200
            
        except Exception as e:
            api.abort(500, f'Error crawling the product: {str(e)}')

