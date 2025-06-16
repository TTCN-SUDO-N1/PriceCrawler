from flask import request, jsonify, Blueprint
from flask_restx import Namespace, Resource
from NewApp.models import Product, ProductCrawl, ProductCrawlLog
from NewApp import db
from apscheduler.schedulers.background import BackgroundScheduler
from SendMail import send_mail_with_product_info
from OCR.screenshot import scrape


api = Namespace('reminder', description='Reminder related operations')
reminder_routes = Blueprint('reminder_routes', __name__)

scheduler = BackgroundScheduler()
scheduler.start()

# Store reminders in memory for simplicity
reminders = []

@api.route('/products/<int:product_id>/set-reminder')
class SetReminder(Resource):
    def post(self, product_id):
        data = request.json
        email = data.get('email')
        if not email:
            return jsonify({'error': 'Email is required'}), 400

        # Add reminder to the list
        reminders.append({'product_id': product_id, 'email': email})

        product = Product.query.get_or_404(product_id)
        product.reminder_email = email
        db.session.commit()

        return {'message': f'Reminder set for product {product.name}'}, 200

@api.route('/schedule-crawl')
class ScheduleCrawl(Resource):
    def post(self):
        data = request.json
        hours = data.get('hours')
        if not hours or not isinstance(hours, (int, float)):
            return jsonify({'error': 'Valid number of hours is required'}), 400

        def crawl_job():
            crawls = ProductCrawl.query.all()
            for crawl in crawls:
                crawl_result = scrape(crawl.link)
                log = ProductCrawlLog(
                    product_crawl_id=crawl.id,
                    name=crawl_result.get('product_name', 'Unknown'),
                    price=crawl_result.get('current_price'),
                    other_data=crawl_result,
                )
                db.session.add(log)
            db.session.commit()

        scheduler.add_job(crawl_job, 'interval', hours=hours)

        return jsonify({'message': f'Crawl scheduled in {hours} hours'}), 200

# Example function to check reminders and send emails
def check_reminders(app):
    with app.app_context():
        for reminder in reminders:
            product_id = reminder['product_id']
            email = reminder['email']

            product = Product.query.get(product_id)
            if not product:
                continue

            # Get all enemy products (crawls) for this product
            crawls = ProductCrawl.query.filter_by(prod_id=product_id).all()
            for crawl in crawls:
                # Get the latest log for this enemy product
                latest_log = ProductCrawlLog.query.filter_by(product_crawl_id=crawl.id).order_by(ProductCrawlLog.timestamp.desc()).first()
                
                # Check if latest enemy price is lower than original product price
                print(f"product.org_price: {product.cur_price}, latest_log.price: {latest_log.price if latest_log else 'No logs'}")
                if (latest_log and 
                    latest_log.price and 
                    product.cur_price and 
                    latest_log.price < product.cur_price):
                    
                    try:
                        # Safely convert prices to float, handling None values
                        enemy_price = float(latest_log.price) if latest_log.price is not None else 0.0
                        original_price = float(product.cur_price) if product.cur_price is not None else 0.0
                        
                        send_mail_with_product_info(
                        to=email,
                        subject='Price Alert - Enemy Product Price Drop!',
                        body=f'Bad The enemy product "{latest_log.name}" on {crawl.enemy.name if crawl.enemy else "competitor site"} is now priced lower than your original product price.',
                        product_name=product.name,
                        enemy_name=latest_log.name,
                        enemy_price=enemy_price,
                        original_price=original_price
                    )
                    except Exception as e:
                        print(f"Failed to send email to {email}: {e}")

                    print(f"Email sent to {email}: Enemy product {latest_log.name} (${latest_log.price}) is lower than {product.name} (${product.org_price})")
                else:
                    print(f"No price drop for {product.name} or no logs found for enemy products.")

