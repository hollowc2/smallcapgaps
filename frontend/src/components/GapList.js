import React, { useState, useRef } from 'react';
import Chart from './Chart';
import IntradayChart from './IntradayChart';

function GapList({ gaps, onSelectGap, expandedGaps, ticker_stats }) {
  console.log('Received ticker_stats in GapList:', ticker_stats);  // Add this line
  const [tooltipInfo, setTooltipInfo] = useState({ visible: false, content: '', position: {} });
  const tooltipRef = useRef(null);

  if (!Array.isArray(gaps) || gaps.length === 0) {
    return <p>No gap data available.</p>;
  }

  const formatNumber = (value) => {
    return typeof value === 'number' ? value.toFixed(2) : 'N/A';
  };

  const getColorClass = (value) => {
    if (typeof value !== 'number') return '';
    return value >= 0 ? 'positive' : 'negative';
  };

  const handleTickerHover = (event, gap) => {
    const rect = event.target.getBoundingClientRect();
    const stats = ticker_stats[gap.ticker] || {};
    console.log(`Hover stats for ${gap.ticker}:`, stats);
    setTooltipInfo({
      visible: true,
      content: `Ticker: ${gap.ticker}\nTotal Gaps: ${stats.total_gaps || 'N/A'}\nChance of Closing Red: ${formatNumber(stats.chance_to_close_red)}%`,
      position: { top: rect.bottom + window.scrollY, left: rect.left + window.scrollX }
    });
  };

  const closeTooltip = () => {
    setTooltipInfo({ ...tooltipInfo, visible: false });
  };

  return (
    <ul className="gap-list">
      {gaps.map((gap) => (
        <React.Fragment key={gap.id}>
          <li 
            onClick={() => onSelectGap(gap)}
            className={`gap-item ${expandedGaps[gap.id] ? 'expanded' : ''}`}
          >
            <div className="gap-content">
              <span 
                className="gap-ticker" 
                onMouseEnter={(e) => handleTickerHover(e, gap)}
                onMouseLeave={closeTooltip}
              >
                {gap.ticker || 'Unknown'}
              </span>
              <span className="gap-date">{gap.date || 'No date'}</span>
              <span className={`gap-percent ${getColorClass(gap.gap_percent)}`}>
                {formatNumber(gap.gap_percent)}%
              </span>
              <span className={`gap-return ${getColorClass(gap.return)}`}>
                {formatNumber(gap.return)}%
              </span>
              <span className={`gap-close ${gap.did_close_red ? 'red' : 'green'}`}>
                Close
              </span>
       
            </div>
          </li>
          
          {expandedGaps[gap.id] && 
            expandedGaps[gap.id].daily_data && 
            expandedGaps[gap.id].intraday_data && 
            expandedGaps[gap.id].intraday_data.length > 0 && (
            <li className="chart-container">
              <div className="charts-inline">
                <div className="chart-wrapper">
                  <Chart 
                    gap={expandedGaps[gap.id]} 
                    data={expandedGaps[gap.id].daily_data} 
                    options={{ width: '100%', height: 400 }} 
                  />
                </div>
                <div className="chart-wrapper">
                  <IntradayChart 
                    gap={expandedGaps[gap.id]} 
                    data={expandedGaps[gap.id].intraday_data} 
                  />
                </div>
              </div>
            </li>
          )}
        </React.Fragment>
      ))}
      {tooltipInfo.visible && (
        <div 
          ref={tooltipRef}
          className="tooltip" 
          style={{
            position: 'absolute',
            top: `${tooltipInfo.position.top}px`,
            left: `${tooltipInfo.position.left}px`,
            backgroundColor: 'white',
            border: '1px solid #ccc',
            padding: '10px',
            borderRadius: '4px',
            boxShadow: '0 2px 5px rgba(0,0,0,0.2)',
            zIndex: 1000,
            color: 'black',
          }}
          onMouseLeave={closeTooltip}
        >
          <pre>{tooltipInfo.content}</pre>
          
        </div>
      )}
    </ul>
  );
}

export default GapList;
