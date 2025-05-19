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


def send_mail(to, subject, body, image_path=None):
    msg = MIMEMultipart()
    msg['From'] = MAIL_DEFAULT_SENDER
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Attach image if provided
    if image_path:
        try:
            with open(image_path, 'rb') as img_file:
                img = MIMEImage(img_file.read())
                img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(image_path))
                msg.attach(img)
        except Exception as e:
            print(f"Failed to attach image: {e}")

    try:
        server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT)
        if MAIL_USE_TLS:
            server.starttls()
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.sendmail(MAIL_DEFAULT_SENDER, to, msg.as_string())
        server.quit()
        print(f"Mail sent to {to}")
    except Exception as e:
        print(f"Failed to send mail: {e}")

if __name__ == "__main__":
    to = 'hoagowo1911@gmail.com'
    subject = 'Send image from my project'
    body = 'See attached image.'
    image_path = os.path.expanduser('~/Pictures/9.png')
    send_mail(to, subject, body, image_path=image_path)

