from flask import request, jsonify, Blueprint
from flask_restx import Namespace, Resource
from NewApp.models import Product, ProductCrawl, ProductCrawlLog
from flask_mail import Message
from NewApp import mail, db
from apscheduler.schedulers.background import BackgroundScheduler
from SendMail import send_email, send_mail_with_product_info
import os
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

        return jsonify({'message': f'Reminder set for product {product.name}'}), 200

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
@scheduler.scheduled_job('interval', minutes=5)
def check_reminders():
    for reminder in reminders:
        product_id = reminder['product_id']
        email = reminder['email']

        product = Product.query.get(product_id)
        if not product:
            continue

        crawls = ProductCrawl.query.filter_by(prod_id=product_id).all()
        for crawl in crawls:
            logs = ProductCrawlLog.query.filter_by(product_crawl_id=crawl.id).order_by(ProductCrawlLog.timestamp.desc()).first()
            if logs and logs.price < product.org_price:
                send_mail_with_product_info(
                    to=email,
                    subject='Price Alert',
                    body=f'The price of enemy product ({crawl.link}) is now below your original product price.',
                    product_name=product.name,
                    enemy_name=logs.name,
                    enemy_price=logs.price,
                    original_price=product.org_price
                )
