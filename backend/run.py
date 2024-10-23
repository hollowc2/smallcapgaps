from app import create_app, db
from app.services import fetch_data, process_gap_data
from app.routes import api_bp
from datetime import date, datetime, time
import os
import pytz
from apscheduler.schedulers.background import BackgroundScheduler

app = create_app()

def scheduled_fetch():
    with app.app_context():
        start_date = date.today().strftime('%Y-%m-%d')
        # fetch_data(start_date)
        # process_gap_data is already called within fetch_data after data insertion

if __name__ == '__main__':
    with app.app_context():
        # Ensure the database is created
        db.create_all()
        #test xommit
        
        
        # # Fetch data on startup
        # start_date = os.getenv("START_DATE", date.today().strftime('%Y-%m-%d'))
        # fetch_data(start_date)
        
        # # After fetching and processing data
        # from app.models import GapData
        # gap_count = GapData.query.count()
        # print(f"Total GapData records: {gap_count}")

        # Schedule daily fetch
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            func=scheduled_fetch,

            trigger='cron',
            hour=13,
            minute=1,
            timezone=pytz.timezone('US/Pacific')
        )
        scheduler.start()
        
    app.run(debug=True, use_reloader=False)