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
        start_date = os.getenv('START_DATE')  # Get from environment
        print(f"Starting scheduled tasks with START_DATE: {start_date}")  # Debug log
        try:
            fetch_data(start_date)
            process_gap_data(start_date)
            update_ticker_stats()
            print("Completed scheduled tasks successfully")
        except Exception as e:
            print(f"Error in scheduled tasks: {str(e)}")

if __name__ == '__main__':
    # Log configuration on startup
    print(f"Starting application with START_DATE: {os.getenv('START_DATE')}")
    
    with app.app_context():
        # Ensure the database is created
        db.create_all()
        
        # Run tasks on startup in a thread, but with better logging
        startup_thread = Thread(target=scheduled_tasks, name="StartupTasks")
        startup_thread.start()
        print("Started initial data fetch in background thread")
        
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
