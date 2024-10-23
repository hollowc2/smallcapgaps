import React, { useEffect, useRef, useState } from 'react';
import { createChart } from 'lightweight-charts';
import { DateTime } from 'luxon';

function IntradayChart({ gap, data }) {
  const chartContainerRef = useRef();
  const [chartSize, setChartSize] = useState({ width: 0, height: 400 });

  useEffect(() => {
    console.log('IntradayChart Props:', { gap, data });
    console.log('First few data points:', data.slice(0, 5));

    if (!data || !Array.isArray(data) || data.length === 0) {
      console.warn('IntradayChart: Invalid or empty data');
      return;
    }

    const updateSize = () => {
      if (chartContainerRef.current) {
        setChartSize({
          width: chartContainerRef.current.clientWidth,
          height: 400
        });
      }
    };

    window.addEventListener('resize', updateSize);
    updateSize();

    return () => window.removeEventListener('resize', updateSize);
  }, [data]);

  useEffect(() => {
    console.log('Rendering IntradayChart with data:', data);

    if (!data || !Array.isArray(data) || data.length === 0 || chartSize.width === 0) {
      console.warn('IntradayChart: Missing or empty data, or chart size not set.');
      return;
    }

    const chart = createChart(chartContainerRef.current, {
      width: chartSize.width,
      height: chartSize.height,
      layout: {
        background: { color: '#ffffff' },
        textColor: '#333',
      },
      grid: {
        vertLines: { color: '#f0f0f0' },
        horzLines: { color: '#f0f0f0' },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        tickMarkFormatter: (time) => {
          const date = new Date(time * 1000);
          return DateTime.fromJSDate(date)
            .setZone('America/Los_Angeles')
            .toFormat('HH:mm');
        },
      },
    });

    const lineSeries = chart.addLineSeries({
      color: '#2196F3',
      lineWidth: 2,
    });

    const formattedData = data.map(item => {
      if (!item || typeof item.timestamp === 'undefined') {
        console.warn('Invalid data item:', item);
        return null;
      }

      // Convert timestamp to Pacific Standard Time
      const pstTime = DateTime.fromMillis(item.timestamp)
        .setZone('America/Los_Angeles');

      return { 
        time: pstTime.toSeconds(),
        value: parseFloat(item.close)
      };
    }).filter(Boolean);

    console.log('Formatted data (first 5 items):', formattedData.slice(0, 5));

    if (formattedData.length > 0) {
      lineSeries.setData(formattedData);
      chart.timeScale().fitContent();
    } else {
      console.warn('No valid data points after formatting');
    }

    return () => {
      chart.remove();
    };
  }, [data, chartSize]);

  return <div ref={chartContainerRef} className="ChartContainer" style={{ width: '100%', height: '400px' }} />;
}

export default IntradayChart;
