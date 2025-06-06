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
    @api.param('product_crawl_id', 'Filter logs by product crawl ID', _in='query')
    @api.marshal_list_with(product_crawl_log_output_model)
    def get(self):
        product_crawl_id = request.args.get('product_crawl_id')
        if product_crawl_id:
            return ProductCrawlLog.query.filter_by(product_crawl_id=product_crawl_id).all(), 200
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

@api.route('/price-history/<int:product_crawl_id>')
@api.param('product_crawl_id', 'Product crawl unique identifier')
@api.response(404, 'Product crawl not found')
class ProductCrawlPriceHistory(Resource):
    @api.doc('get_price_history', description='Get price history for a product crawl with chart data')
    def get(self, product_crawl_id):
        # First verify the product crawl exists
        from NewApp.models import ProductCrawl
        product_crawl = ProductCrawl.query.get_or_404(product_crawl_id)
        
        # Get all logs for this product crawl, ordered by timestamp
        logs = ProductCrawlLog.query.filter_by(product_crawl_id=product_crawl_id).order_by(ProductCrawlLog.timestamp.asc()).all()
        
        if not logs:
            return {
                'product_crawl': {
                    'id': product_crawl.id,
                    'link': product_crawl.link,
                    'product': product_crawl.product.name if product_crawl.product else None,
                    'enemy': product_crawl.enemy.name if product_crawl.enemy else None
                },
                'price_history': [],
                'chart_data': {
                    'labels': [],
                    'prices': [],
                    'latest_price': None,
                    'price_trend': 'stable',
                    'price_change': 0
                }
            }, 200
        
        # Prepare chart data
        labels = []
        prices = []
        valid_logs = []
        
        for log in logs:
            if log.price is not None:
                labels.append(log.timestamp.strftime('%Y-%m-%d %H:%M'))
                prices.append(float(log.price))
                valid_logs.append({
                    'id': log.id,
                    'timestamp': log.timestamp.isoformat(),
                    'price': float(log.price),
                    'name': log.name
                })
        
        # Calculate price trend and change
        latest_price = prices[-1] if prices else None
        price_trend = 'stable'
        price_change = 0
        
        if len(prices) >= 2:
            first_price = prices[0]
            last_price = prices[-1]
            price_change = last_price - first_price
            
            if price_change > 0:
                price_trend = 'increasing'
            elif price_change < 0:
                price_trend = 'decreasing'
        
        return {
            'product_crawl': {
                'id': product_crawl.id,
                'link': product_crawl.link,
                'product': product_crawl.product.name if product_crawl.product else None,
                'enemy': product_crawl.enemy.name if product_crawl.enemy else None
            },
            'price_history': valid_logs,
            'chart_data': {
                'labels': labels,
                'prices': prices,
                'latest_price': float(latest_price) if latest_price is not None else None,
                'price_trend': price_trend,
                'price_change': float(price_change) if price_change != 0 else 0,
                'total_records': len(valid_logs)
            }
        }, 200
