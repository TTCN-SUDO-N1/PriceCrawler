from NewApp import create_app
from apscheduler.schedulers.background import BackgroundScheduler
from NewApp.routes.reminder_routes import check_reminders
from dotenv import load_dotenv
import os
load_dotenv()

intervalMailSend = os.getenv("Interval_Mail_Sent", "1") 
app = create_app()
scheduler = BackgroundScheduler()


if __name__ == '__main__':
    with app.app_context():
        scheduler.add_job(check_reminders, 'interval', minutes=intervalMailSend, args=[app])  # Pass app to the job
        scheduler.start()
        app.run(debug=True)