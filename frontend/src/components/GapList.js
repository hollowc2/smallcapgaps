import React from 'react';
import Chart from './Chart';
import IntradayChart from './IntradayChart';

function GapList({ gaps, onSelectGap, expandedGaps }) {
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

  return (
    <ul className="gap-list">
      {gaps.map((gap) => (
        <React.Fragment key={gap.id}>
          <li 
            onClick={() => onSelectGap(gap)}
            className={`gap-item ${expandedGaps[gap.id] ? 'expanded' : ''}`}
          >
            <div className="gap-content">
              <span className="gap-ticker">{gap.ticker || 'Unknown'}</span>
              <span className="gap-date">{gap.date || 'No date'}</span>
              <span className={`gap-percent ${getColorClass(gap.gap_percent)}`}>
                Gap: {formatNumber(gap.gap_percent)}%
              </span>
              <span className={`gap-return ${getColorClass(gap.return)}`}>
                Return: {formatNumber(gap.return)}%
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
    </ul>
  );
}

export default GapList;
