import React, { useState, useEffect } from 'react';
import SearchForm from './components/SearchForm';
import GapList from './components/GapList';
import Chart from './components/Chart';
import IntradayChart from './components/IntradayChart';
import './App.css';
import { fetchGapData, fetchDailyData, fetchIntradayData, fetchTickerStats } from './api';
import { v4 as uuidv4 } from 'uuid'; // Ensure uuid is installed: npm install uuid
import { DateTime } from 'luxon';

function App() {
  const [gapData, setGapData] = useState([]);
  const [expandedGaps, setExpandedGaps] = useState({}); // { [gapId]: gapObject }
  const [loading, setLoading] = useState(false); // State for loading
  const [error, setError] = useState(null); // State for errors
  const [tickerStats, setTickerStats] = useState({});

  const handleSearch = async (searchParams) => {
    console.log('Searching with params:', searchParams);
    try {
      setLoading(true);
      setError(null);
      const data = await fetchGapData(searchParams);
      console.log('Received data:', data);
      
      // Sort the data by gap_percent in descending order and assign unique IDs
      const sortedData = data
        .sort((a, b) => b.gap_percent - a.gap_percent)
        .map(gap => ({ ...gap, id: uuidv4() })); // Assign unique ID
      
      setGapData(sortedData);
      setExpandedGaps({}); // Reset expanded gaps on new search
    } catch (error) {
      console.error('Error fetching gap data:', error);
      setError('Failed to fetch gap data.');
      setGapData([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const fetchStats = async () => {
      const uniqueTickers = [...new Set(gapData.map(gap => gap.ticker))];
      const stats = {};
      for (const ticker of uniqueTickers) {
        try {
          const tickerStat = await fetchTickerStats(ticker);
          stats[ticker] = tickerStat; // This should now be an object, not an array
          console.log(`Fetched stats for ${ticker}:`, tickerStat);
        } catch (error) {
          console.error(`Failed to fetch stats for ${ticker}:`, error);
        }
      }
      setTickerStats(stats);
      console.log('All ticker stats:', stats);
    };

    if (gapData.length > 0) {
      fetchStats();
    }
  }, [gapData]);

  const handleGapSelect = async (gap) => {
    console.log('Gap clicked:', gap);
    
    // Toggle expansion
    if (expandedGaps[gap.id]) {
      // If already expanded, collapse it
      const newExpandedGaps = { ...expandedGaps };
      delete newExpandedGaps[gap.id];
      setExpandedGaps(newExpandedGaps);
      return;
    }

    // If the gap already has the necessary data, expand it
    if (gap.daily_data && gap.intraday_data) {
      setExpandedGaps(prev => ({ ...prev, [gap.id]: gap }));
      return;
    }

    // Else, fetch the missing data
    try {
      setLoading(true);
      setError(null);

      const { ticker, date } = gap;

      if (!ticker || !date) {
        console.warn('Gap lacks ticker or date, cannot fetch data.');
        setError('Selected gap lacks ticker or date, unable to fetch data.');
        return;
      }

      const dailyData = await fetchDailyData({ ticker, start_date: date, end_date: date });
      console.log('Fetched Daily Data:', dailyData);

      const intradayData = await fetchIntradayData({ ticker, date });
      console.log('Fetched Intraday Data:', intradayData);

      const updatedGap = { 
        ...gap, 
        daily_data: dailyData, 
        intraday_data: intradayData 
      };

      setGapData(prevGaps => prevGaps.map(g => g.id === gap.id ? updatedGap : g));
      setExpandedGaps(prev => ({ ...prev, [gap.id]: updatedGap }));
    } catch (error) {
      console.error('Error fetching additional data for the selected gap:', error);
      setError('Failed to fetch additional data for the selected gap.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <h1>Small Cap Gaps</h1>
      <SearchForm onSearch={handleSearch} />
      
      {loading && <p>Loading...</p>}
      {error && <p className="error">{error}</p>}
      
      <GapList 
        gaps={gapData} 
        onSelectGap={handleGapSelect} 
        expandedGaps={expandedGaps} 
        ticker_stats={tickerStats}
      />
    </div>
  );
}

export default App;
