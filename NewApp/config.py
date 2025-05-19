import os
from dotenv import load_dotenv
from datetime import timedelta

# Load .env file
load_dotenv()

# Get variable from env file
db_type = os.getenv("DB_TYPE")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")
db_host = os.getenv("DB_HOST")
secret_key = os.getenv("SECRET_KEY")


class Config:
    SQLALCHEMY_DATABASE_URI = f'{db_type}://{db_user}:{db_password}@{db_host}/{db_name}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    
    # Mail settings
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@example.com')