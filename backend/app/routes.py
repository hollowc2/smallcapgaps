from flask import Blueprint, request, jsonify
from app.models import GapData, IntradayDataConcrete, DailyDataConcrete, TickerStats
from app import db
from datetime import datetime
from sqlalchemy import func

api_bp = Blueprint('api', __name__)

@api_bp.route('/gap_stats', methods=['GET'])
def get_gap_stats():
    ticker = request.args.get('ticker')
    date_str = request.args.get('date')

    query = GapData.query

    if ticker:
        query = query.filter(GapData.ticker == ticker.upper())
    if date_str:
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            query = query.filter(GapData.date == date_obj)
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    gap_stats = query.all()
    results = []
    for gap in gap_stats:
        results.append({
            'ticker': gap.ticker,
            'date': gap.date.strftime('%Y-%m-%d'),
            'gap_percent': gap.gap_percent,
            'return': gap.return_value,
            'did_close_red': gap.did_close_red,
            'start_chart_date': gap.start_chart_date.strftime('%Y-%m-%d %H:%M:%S'),
            'end_chart_date': gap.end_chart_date.strftime('%Y-%m-%d %H:%M:%S'),
            'intraday_data': gap.intraday_data,  
            'daily_data': gap.daily_data
        })

    return jsonify(results), 200

@api_bp.route('/daily_data', methods=['GET'])
def get_daily_data():
    ticker = request.args.get('ticker')
    date_str = request.args.get('date')

    query = DailyDataConcrete.query  # Use concrete model

    if ticker:
        query = query.filter(DailyDataConcrete.ticker == ticker.upper())
    if date_str:
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            query = query.filter(DailyDataConcrete.date == date_obj)
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    daily_data = query.all()
    results = []
    for data in daily_data:
        results.append({
            'ticker': data.ticker,
            'date': data.date.strftime('%Y-%m-%d'),
            'open': data.open,
            'high': data.high,
            'low': data.low,
            'close': data.close,
            'volume': data.volume,
            'volume_weighted_avg_price': data.volume_weighted_avg_price
        })

    return jsonify(results), 200    

@api_bp.route('/intraday_data', methods=['GET'])
def get_intraday_data():
    ticker = request.args.get('ticker')
    date_str = request.args.get('date')
    
    if not ticker or not date_str:
        return jsonify({'error': 'Ticker and date are required'}), 400
    
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    query = IntradayDataConcrete.query.filter(IntradayDataConcrete.ticker == ticker.upper())
    
    # Correct filter based on timestamp
    query = query.filter(func.date(IntradayDataConcrete.timestamp) == date_obj)
    
    intraday_data = query.all()
    results = []
    for data in intraday_data:
        results.append({
            'ticker': data.ticker,
            'timestamp': data.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'open': data.open,
            'high': data.high,
            'low': data.low,
            'close': data.close,
            'volume': data.volume,
            'volume_weighted_avg_price': data.volume_weighted_avg_price
        })

    return jsonify(results), 200

@api_bp.route('/ticker_stats', methods=['GET'])
def get_ticker_stats():
    ticker = request.args.get('ticker')
    
    if ticker:
        ticker_stat = TickerStats.query.get(ticker.upper())
        if ticker_stat:
            return jsonify([ticker_stat.to_dict()]), 200
        else:
            return jsonify([]), 200  # Return an empty array if no stats found
    else:
        # If no ticker is provided, return stats for all tickers
        all_stats = TickerStats.query.all()
        results = [stat.to_dict() for stat in all_stats]
        return jsonify(results), 200
