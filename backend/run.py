from app import create_app, db
from app.services import fetch_data, process_gap_data, update_ticker_stats
from app.routes import api_bp
from datetime import date, datetime, time
import os
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from threading import Thread

app = create_app()

def scheduled_tasks():
    with app.app_context():
        start_date = date.today().strftime('%Y-%m-%d')
        fetch_data(start_date)
        process_gap_data(start_date)
        update_ticker_stats()

if __name__ == '__main__':
    with app.app_context():
        # Ensure the database is created
        db.create_all()
        
        # Run tasks on startup
        Thread(target=scheduled_tasks).start()
        
        # Schedule daily tasks
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            func=scheduled_tasks,
            trigger='cron',
            hour=13,
            minute=0,
            day_of_week='mon-fri',
            timezone=pytz.timezone('US/Pacific')
        )
        scheduler.start()
        
    app.run(debug=True, use_reloader=False)
