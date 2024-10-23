import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000/api"

def test_gap_stats():
    print("\nTesting Gap Stats:")
    response = requests.get(f"{BASE_URL}/gap_stats", params={"ticker": "PEGY", "date": "2024-10-04"})
    print("Status Code:", response.status_code)
    print("Response:", response.json())

def test_gap_stats_by_date():
    print("\nTesting Gap Stats by Date:")
    response = requests.get(f"{BASE_URL}/gap_stats", params={"date": "2024-10-04"})
    print("Status Code:", response.status_code)
    print("Response:", response.json())

def test_gap_stats_by_ticker():
    print("\nTesting Gap Stats by Ticker:")
    response = requests.get(f"{BASE_URL}/gap_stats", params={"ticker": "PEGY"})
    print("Status Code:", response.status_code)
    print("Response:", response.json())




if __name__ == "__main__":
    test_gap_stats()
    test_gap_stats_by_date()
    test_gap_stats_by_ticker()
    # test_intraday_data()
    # test_stock_data()