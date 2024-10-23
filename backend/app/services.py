import requests
import time
import logging
from datetime import datetime, timedelta, date
from app import db, create_app  # Ensure this imports the correct db instance
from app.models import GroupedDailyBars, GapData, DailyDataConcrete
from sqlalchemy.exc import SQLAlchemyError
import os
from dotenv import load_dotenv
from flask import current_app
from sqlalchemy import func
from requests.exceptions import RequestException, HTTPError
from time import sleep
import json
from app.rate_limiter import make_api_request
from collections import deque
from sqlalchemy.orm import joinedload

load_dotenv()

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API key and start date from environment variables
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
START_DATE = os.getenv("START_DATE")  # Ensure this is set in your .env

delayed_symbols = deque(maxlen=100)  # Store up to 100 delayed symbols

def data_exists_for_date(date):
    """
    Check if data already exists in the database for a given date.
    """
    start_of_day = datetime.combine(date, datetime.min.time())
    end_of_day = datetime.combine(date, datetime.max.time())
    
    query = db.session.query(GroupedDailyBars).filter(
        GroupedDailyBars.timestamp.between(start_of_day, end_of_day)
    )
    count = query.count()
    logger.info(f"Found {count} records for date {date}")
    
    if count > 0:
        sample_records = query.limit(5).all()
        for record in sample_records:
            logger.info(f"Sample record: {record.symbol} on {record.timestamp}")
    else:
        logger.warning(f"No records found for date {date}")
    
    return count > 0

def fetch_data(start_date=None):
    app = create_app()
    with app.app_context():
        logger.info(f"Fetching data starting from: {start_date or START_DATE}")
        
        if not start_date:
            start_date = START_DATE

        try:
            fetch_start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            logger.error(f"Invalid start date format: {start_date}. Should be YYYY-MM-DD.")
            return

        today = datetime.today().date()
        if fetch_start_date > today:
            logger.error("Start date is in the future.")
            return

        current_date = fetch_start_date

        while current_date <= today:
            logger.info(f"Processing date: {current_date}")

            if data_exists_for_date(current_date):
                logger.info(f"Data for {current_date} already exists in the database.")
                # Process gap data even if the data already exists
                process_gap_data(current_date, current_date)
                current_date += timedelta(days=1)
                continue

            logger.info(f"Fetching data for date: {current_date}")

            # Correctly construct the API URL with the current_date
            api_url = f"https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{current_date}?adjusted=true&apiKey={POLYGON_API_KEY}"
            
            logger.debug(f"API URL for {current_date}: {api_url}")

            max_retries = 5
            retry_delay = 60  # Initial delay of 60 seconds

            for attempt in range(max_retries):
                try:
                    logger.debug(f"Requesting URL: {api_url}")
                    response = make_api_request('GET', api_url)
                    response.raise_for_status()
                    break  # If successful, break out of the retry loop
                except HTTPError as e:
                    if e.response.status_code == 429:
                        logger.warning(f"Rate limit exceeded. Attempt {attempt + 1}/{max_retries}. Retrying in {retry_delay} seconds.")
                        sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        logger.error(f"HTTP error occurred: {e}")
                        break  # Exit the retry loop for non-rate-limit errors
                except RequestException as e:
                    logger.error(f"Failed to fetch data for {current_date}: {e}")
                    break  # Exit the retry loop for other request exceptions
            else:
                logger.error(f"Failed to fetch data for {current_date} after {max_retries} attempts.")
                current_date += timedelta(days=1)
                continue

            data = response.json()
            if data.get('status') != 'OK':
                logger.error(f"API response error for {current_date}: {data.get('status')}")
                time.sleep(60)
                current_date += timedelta(days=1)
                continue

            results = data.get('results', [])
            logger.info(f"Number of records fetched for {current_date}: {len(results)}")

            if len(results) == 0:
                logger.warning(f"No results returned for {current_date}")

            for record in results:
                try:
                    symbol = record.get('T', '')  # 'T' is the field for symbol

                    # Check if this specific record already exists
                    timestamp = datetime.combine(current_date, datetime.min.time())
                    existing_record = GroupedDailyBars.query.filter_by(
                        symbol=symbol,
                        timestamp=timestamp
                    ).first()

                    if existing_record:
                        logger.debug(f"Record for {symbol} on {current_date} already exists. Skipping.")
                        continue

                    # Safely extract values with defaults
                    volume = int(record.get('v', 0))
                    open_price = float(record.get('o', 0.0))
                    close_price = float(record.get('c', 0.0))
                    high_price = float(record.get('h', 0.0))
                    low_price = float(record.get('l', 0.0))
                    num_transactions = int(record.get('n', 0))
                    
                    # Handle 'vw' (volume weighted average price)
                    vw = record.get('vw')
                    if vw is None or vw == '':
                        vw = 0.0
                    else:
                        try:
                            vw = float(vw)
                        except ValueError:
                            logger.warning(f"Invalid 'vw' value for {symbol} on {current_date}: {vw}. Setting to 0.0.")
                            vw = 0.0

                    grouped_bar = GroupedDailyBars(
                        symbol=symbol,
                        open=open_price,
                        close=close_price,
                        high=high_price,
                        low=low_price,
                        number_of_transactions=num_transactions,
                        timestamp=timestamp,
                        volume=volume,
                        volume_weighted_avg_price=vw
                    )
                    db.session.add(grouped_bar)
                    logger.debug(f"Added GroupedDailyBars record for {symbol} on {current_date}")
                    
                except Exception as e:
                    logger.error(f"Error processing record {record}: {e}")

            try:
                db.session.commit()
                logger.info(f"Data for {current_date} committed to the database.")
            except SQLAlchemyError as e:
                db.session.rollback()
                logger.error(f"Database commit failed for {current_date}: {e}")

            # Process gap data for the current date
            process_gap_data(current_date, current_date)

            # Adjust the sleep time at the end of each iteration
      
            current_date += timedelta(days=1)

def process_gap_data(start_date, end_date=None):
    app = current_app._get_current_object()
    with app.app_context():
        logger.info(f"Processing gap data from {start_date} to {end_date or 'present'}")

        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        if end_date is None:
            end_date = datetime.now().date()
        elif isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        current_date = start_date
        while current_date <= end_date:
            logger.info(f"Processing gap data for {current_date}")

            try:
                # Fetch data for the previous day
                previous_date = current_date - timedelta(days=1)
                previous_bars = GroupedDailyBars.query.filter(
                    func.date(GroupedDailyBars.timestamp) == previous_date
                ).all()
                logger.info(f"Found {len(previous_bars)} bars for previous date {previous_date}")
                previous_close_dict = {bar.symbol: bar.close for bar in previous_bars}

                # Fetch data for the current day
                current_bars = GroupedDailyBars.query.filter(
                    func.date(GroupedDailyBars.timestamp) == current_date
                ).all()
                logger.info(f"Found {len(current_bars)} bars for current date {current_date}")

                for bar in current_bars:
                    previous_close = previous_close_dict.get(bar.symbol)
                    if not previous_close:
                        logger.debug(f"No previous close for {bar.symbol} on {current_date}. Skipping.")
                        continue

                    # Calculate gap_percent
                    gap_percent = ((bar.open - previous_close) / previous_close) * 100

                    # Only process if gap_percent > 20 and volume > 1,000,000
                    if gap_percent > 20 and bar.volume > 1_000_000:
                        logger.info(f"Found potential gap for {bar.symbol} on {current_date}: {gap_percent:.2f}% gap, {bar.volume} volume")

                        # Calculate return
                        return_value = ((bar.close - bar.open) / bar.open) * 100
                        did_close_red = bar.close < bar.open

                        # Fetch intraday data
                        intraday_data = fetch_intraday_data(bar.symbol, current_date)
                        
                        # Fetch daily data for a 60-day range around the current date
                        start_chart_date = current_date - timedelta(days=30)
                        end_chart_date = current_date + timedelta(days=30)
                        daily_data = fetch_daily_data(bar.symbol, start_chart_date, end_chart_date)

                        # Only proceed if both intraday and daily data are available
                        if intraday_data is not None and daily_data is not None:
                            # Check if gap data already exists for this specific symbol and date
                            existing_gap_data = GapData.query.filter_by(
                                ticker=bar.symbol,
                                date=current_date
                            ).first()

                            if existing_gap_data:
                                # Update existing data
                                existing_gap_data.gap_percent = gap_percent
                                existing_gap_data.return_value = return_value
                                existing_gap_data.did_close_red = did_close_red
                                existing_gap_data.intraday_data = intraday_data
                                existing_gap_data.daily_data = daily_data
                                logger.info(f"Updated gap data for {bar.symbol} on {current_date}")
                            else:
                                # Add new gap data
                                new_gap_data = GapData(
                                    ticker=bar.symbol,
                                    date=current_date,
                                    gap_percent=gap_percent,
                                    return_value=return_value,
                                    did_close_red=did_close_red,
                                    start_chart_date=start_chart_date,
                                    end_chart_date=end_chart_date,
                                    intraday_data=intraday_data,
                                    daily_data=daily_data
                                )
                                db.session.add(new_gap_data)
                                logger.info(f"Added new gap data for {bar.symbol} on {current_date}")
                        else:
                            logger.warning(f"Skipping gap data for {bar.symbol} on {current_date} due to missing data")

                # Commit changes after processing all bars for the current date
                db.session.commit()
                logger.info(f"Committed gap data changes for {current_date} to the database.")

            except Exception as e:
                db.session.rollback()
                logger.error(f"Error processing gap data for {current_date}: {e}")
                logger.exception("Exception details:")

            # Move to the next day
            current_date += timedelta(days=1)

def fetch_intraday_data(symbol, date):
    date_str = date.strftime('%Y-%m-%d')
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/minute/{date_str}/{date_str}?adjusted=true&sort=asc&limit=50000&apiKey={POLYGON_API_KEY}"
    
    try:
        response = make_api_request('GET', url)
        data = response.json()
        
        if data['status'] == 'OK' and 'results' in data:
            intraday_data = []
            for result in data['results']:
                intraday_data.append({
                    'timestamp': result['t'],
                    'open': result['o'],
                    'high': result['h'],
                    'low': result['l'],
                    'close': result['c'],
                    'volume': result['v'],
                    'volume_weighted_avg_price': result.get('vw', 0)
                })
            
            return intraday_data
        else:
            logger.warning(f"No intraday data available for {symbol} on {date_str}. API response: {data}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching intraday data for {symbol} on {date_str}: {e}")
        return None

def fetch_daily_data(symbol: str, start_date, end_date):
    # Ensure end_date is a date object
    if isinstance(end_date, datetime):
        end_date = end_date.date()
    elif not isinstance(end_date, date):
        logger.error(f"end_date must be a date or datetime object, got {type(end_date)}")
        return None

    today = date.today()
    if end_date > today:
        logger.info(f"End date {end_date} is in the future. Setting end date to today {today}.")
        end_date = today

    # Ensure start_date is a date object
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    elif not isinstance(start_date, date):
        logger.error(f"start_date must be a date or datetime object, got {type(start_date)}")
        return None

    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    api_url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{start_date_str}/{end_date_str}?adjusted=true&sort=asc&apiKey={POLYGON_API_KEY}"
    params = {
        'adjusted': 'true',
        'sort': 'asc',
        'limit': 50000,
        'apiKey': POLYGON_API_KEY
    }
    
    logger.info(f"Fetching daily data for {symbol} from {start_date_str} to {end_date_str}")
    
    try:
        daily_data = make_api_request('GET', api_url, params=params)
        daily_data = daily_data.json()
        if not isinstance(daily_data, dict):
            logger.error(f"Unexpected response format for {symbol}: {daily_data}")
            return None

        if 'results' not in daily_data or not daily_data['results']:
            logger.error(f"No results found for {symbol}: {daily_data.get('status')}")
            return None

        return daily_data['results']

    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching daily data for {symbol}: {e}", exc_info=True)
        return None

def retry_delayed_symbols():
    while delayed_symbols:
        symbol, start_date, end_date = delayed_symbols.popleft()
        logger.info(f"Retrying fetch for delayed symbol: {symbol}")
        fetch_daily_data(symbol, start_date, end_date)