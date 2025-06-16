import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', MAIL_USERNAME)

def send_mail_with_product_info(to, subject, body, product_name, enemy_name, enemy_price, original_price):
    msg = MIMEMultipart()
    msg['From'] = MAIL_DEFAULT_SENDER
    msg['To'] = to
    msg['Subject'] = subject

    # Create the email body with product information
    product_info = f"Original Product: {product_name}\nEnemy Product: {enemy_name}\nEnemy Price: {enemy_price}\nCurrent Product Original Price: {original_price}\n\n{body}"
    msg.attach(MIMEText(product_info, 'plain'))

    try:
        server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT)
        if MAIL_USE_TLS:
            server.starttls()
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.sendmail(MAIL_DEFAULT_SENDER, to, msg.as_string())
        server.quit()
        print(f"Mail sent to {to} with product info")
    except Exception as e:
        print(f"Failed to send mail: {e}")

