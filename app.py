from NewApp import create_app
from flask import send_from_directory, current_app
import os
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
from flask_mail import Mail, Message
from NewApp.models import Product, Enemy, ProductCrawl
from NewApp import db

app = create_app()

# Configure mail settings
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')
mail = Mail(app)

# Scheduled crawling function
def scheduled_crawl():
    print("Starting scheduled crawl...")
    products = Product.query.all()
    for product in products:
        enemies = Enemy.query.filter_by(product_id=product.id).all()
        for enemy in enemies:
            try:
                # Perform crawling logic here
                print(f"Crawling enemy product: {enemy.name} for original product: {product.name}")
                # Update product crawl logs, etc.
            except Exception as e:
                print(f"Error crawling enemy product: {str(e)}")

# Reminder function
def check_price_and_send_reminder():
    print("Checking prices and sending reminders...")
    products = Product.query.all()
    for product in products:
        enemies = Enemy.query.filter_by(product_id=product.id).all()
        for enemy in enemies:
            if enemy.price < product.price:
                try:
                    msg = Message(
                        subject=f"Price Alert: {enemy.name} is cheaper than {product.name}",
                        recipients=[os.getenv('USER_EMAIL')],
                        body=f"The price of {enemy.name} ({enemy.price}) is lower than {product.name} ({product.price})."
                    )
                    mail.send(msg)
                    print(f"Reminder sent for product: {product.name}")
                except Exception as e:
                    print(f"Error sending reminder: {str(e)}")

# Schedule tasks
scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_crawl, 'interval', hours=int(os.getenv('CRAWL_INTERVAL_HOURS', 24)))
scheduler.add_job(check_price_and_send_reminder, 'interval', hours=int(os.getenv('REMINDER_INTERVAL_HOURS', 24)))
scheduler.start()

@app.route('/')
def index():
    return "Product Price Crawler API is running."

if __name__ == '__main__':
    app.run(debug=True)