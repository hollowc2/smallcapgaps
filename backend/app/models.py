# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from app import db



class GroupedDailyBars(db.Model):
    __tablename__ = 'grouped_daily_bars'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)  # t-symbol
    close = db.Column(db.Float, nullable=False)         # c-close
    high = db.Column(db.Float, nullable=False)          # h-high
    low = db.Column(db.Float, nullable=False)           # l-low
    number_of_transactions = db.Column(db.Integer, nullable=False)  # n-number of transactions
    open = db.Column(db.Float, nullable=False)          # o-open
    timestamp = db.Column(db.DateTime, nullable=False)  # t-timestamp
    volume = db.Column(db.Integer, nullable=False)      # v-volume
    volume_weighted_avg_price = db.Column(db.Float, nullable=False)  # vw-volume weighted average price

    def __repr__(self):
        return f'<GroupedDailyBars {self.symbol} on {self.timestamp}>'

class GapData(db.Model):
    __tablename__ = 'gap_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    gap_percent = db.Column(db.Float, nullable=True)   # Changed to nullable=True
    return_value = db.Column(db.Float, nullable=True)  # Changed to nullable=True
    did_close_red = db.Column(db.Boolean, nullable=False)  
    start_chart_date = db.Column(db.DateTime, nullable=False)  
    end_chart_date = db.Column(db.DateTime, nullable=False) 
    intraday_data = db.Column(db.JSON, nullable=True)
    daily_data = db.Column(db.JSON, nullable=True)
    
    
    __table_args__ = (
        db.Index('ix_gap_stats_ticker_date', 'ticker', 'date'),
    )

    def __repr__(self):
        return f'<GapData {self.ticker} on {self.date}>'


class IntradayData(db.Model):
    __abstract__ = True

    # Define common columns or methods here
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    open = db.Column(db.Float, nullable=False)
    high = db.Column(db.Float, nullable=False)
    low = db.Column(db.Float, nullable=False)
    close = db.Column(db.Float, nullable=False)
    volume = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<IntradayData {self.timestamp}>'


class DailyData(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    open = db.Column(db.Float, nullable=False)
    high = db.Column(db.Float, nullable=False)
    low = db.Column(db.Float, nullable=False)
    close = db.Column(db.Float, nullable=False)
    volume = db.Column(db.Integer, nullable=False)
    adjusted_close = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f'<DailyData {self.date}>'


class IntradayDataConcrete(IntradayData):
    __tablename__ = 'intraday_data_concrete'
    ticker = db.Column(db.String(10), nullable=False)  # Add ticker field

    def __repr__(self):
        return f'<IntradayDataConcrete {self.ticker} on {self.timestamp}>'

class DailyDataConcrete(DailyData):
    __tablename__ = 'daily_data_concrete'
    ticker = db.Column(db.String(10), nullable=False)  # Add ticker field

    def __repr__(self):
        return f'<DailyDataConcrete {self.ticker} on {self.date}>'
