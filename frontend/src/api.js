const API_BASE_URL = 'http://localhost:5000/api';

export async function fetchDailyData({ ticker, start_date, end_date }) {
  const queryString = new URLSearchParams({ ticker, start_date, end_date }).toString();
  const response = await fetch(`${API_BASE_URL}/daily_data?${queryString}`);
  if (!response.ok) {
    throw new Error('Failed to fetch daily data');
  }
  return response.json();
}

export async function fetchIntradayData({ ticker, date }) {
  const queryString = new URLSearchParams({ ticker, date }).toString();
  const response = await fetch(`${API_BASE_URL}/intraday_data?${queryString}`);
  if (!response.ok) {
    throw new Error('Failed to fetch intraday data');
  }
  return response.json();
}

export async function fetchGapData(searchParams) {
  const { ticker, date } = searchParams;
  const params = {};

  if (ticker) {
    params.ticker = ticker;
  }
  if (date) {
    params.date = date;
  }

  const queryString = new URLSearchParams(params).toString();
  const response = await fetch(`${API_BASE_URL}/gap_stats?${queryString}`);
  if (!response.ok) {
    throw new Error('Failed to fetch gap data');
  }
  return response.json();
}
