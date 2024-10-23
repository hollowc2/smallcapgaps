import React, { useEffect, useRef, useState } from 'react';
import { createChart } from 'lightweight-charts';

function Chart({ gap, data, options = {} }) {
  const chartContainerRef = useRef();
  const [chartSize, setChartSize] = useState({ width: 0, height: 400 });

  useEffect(() => {
    const updateSize = () => {
      if (chartContainerRef.current) {
        setChartSize({
          width: chartContainerRef.current.clientWidth - 10, // Subtract 10px for safety
          height: 400
        });
      }
    };

    window.addEventListener('resize', updateSize);
    updateSize();

    return () => window.removeEventListener('resize', updateSize);
  }, []);

  useEffect(() => {
    if (!gap || !data || data.length === 0 || chartSize.width === 0) return;

    const {
      width = 500,
      height = 300,
      showVolume = false,
      showVWAP = false,
      showTransactions = false,
      focusOnGap = true,
      timeFormat = 'milliseconds',
    } = options;

    const chart = createChart(chartContainerRef.current, {
      width: chartSize.width,
      height: chartSize.height,
      layout: {
        background: { color: '#2c3e50' },
        textColor: '#ecf0f1',
      },
      grid: {
        vertLines: { color: 'rgba(236, 240, 241, 0.1)' },
        horzLines: { color: 'rgba(236, 240, 241, 0.1)' },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        borderColor: '#ecf0f1',
      },
      rightPriceScale: {
        borderColor: '#ecf0f1',
        autoScale: true,
        scaleMargins: {
          top: 0.1,
          bottom: 0.1,
        },
      },
      crosshair: {
        vertLine: {
          color: 'rgba(236, 240, 241, 0.5)',
          width: 1,
          style: 1,
        },
        horzLine: {
          color: 'rgba(236, 240, 241, 0.5)',
          width: 1,
          style: 1,
        },
      },
    });

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#2ecc71',
      downColor: '#e74c3c',
      borderVisible: false,
      wickUpColor: '#2ecc71',
      wickDownColor: '#e74c3c',
    });

    const formattedData = data.map(item => ({
      time: timeFormat === 'milliseconds' ? item.t / 1000 : item.date,
      open: parseFloat(item.o || item.open) || 0,
      high: parseFloat(item.h || item.high) || 0,
      low: parseFloat(item.l || item.low) || 0,
      close: parseFloat(item.c || item.close) || 0,
      volume: item.v || 0,
      vwap: item.vw || 0,
      transactions: item.n || 0,
    }));

    candlestickSeries.setData(formattedData);

    if (showVolume) {
      const volumeSeries = chart.addHistogramSeries({
        color: '#26a69a',
        priceFormat: { type: 'volume' },
        priceScaleId: 'volume',
        scaleMargins: { top: 0.8, bottom: 0 },
      });
      volumeSeries.setData(formattedData.map(item => ({
        time: item.time,
        value: item.volume,
        color: item.close > item.open ? 'rgba(38, 166, 154, 0.5)' : 'rgba(239, 83, 80, 0.5)',
      })));
    }

    if (showVWAP) {
      const vwapSeries = chart.addLineSeries({
        color: 'rgba(255, 192, 0, 0.8)',
        lineWidth: 2,
        priceScaleId: 'right',
      });
      const vwapData = calculateVWAP(data);
      vwapSeries.setData(vwapData);
    }

    if (showTransactions) {
      const transactionsSeries = chart.addLineSeries({
        color: 'rgba(76, 175, 80, 0.8)',
        lineWidth: 2,
        priceScaleId: 'left',
      });
      const emaData = calculateEMA(data, 20); // Example period
      transactionsSeries.setData(emaData);
    }

    // Add a marker for the gap
    const gapDate = gap.date; // Use the gap date directly
    const gapIndex = formattedData.findIndex(item => {
      const itemDate = new Date(item.time * 1000).toISOString().split('T')[0];
      return itemDate === gapDate;
    });
    
    if (gapIndex !== -1) {
      const markerTime = formattedData[gapIndex].time;
      candlestickSeries.setMarkers([
        {
          time: markerTime,
          position: 'aboveBar',
          color: 'white',
          shape: 'arrowDown',
          text: 'Gap',
        },
      ]);

      if (focusOnGap) {
        const rangeStart = Math.max(0, gapIndex - 10);
        const rangeEnd = Math.min(formattedData.length - 1, gapIndex + 10);
        
        chart.timeScale().setVisibleRange({
          from: formattedData[rangeStart].time,
          to: formattedData[rangeEnd].time,
        });
      } else {
        chart.timeScale().fitContent();
      }
    } else {
      console.warn('Gap date not found in the data');
      chart.timeScale().fitContent();
    }

    const handleResize = () => {
      const newWidth = chartContainerRef.current.clientWidth - 10; // Subtract 10px for safety
      chart.applyOptions({ 
        width: newWidth,
        height: chartSize.height 
      });
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [gap, data, options, chartSize]);

  // VWAP Calculation Function
  const calculateVWAP = (data) => {
    let cumulativePV = 0;
    let cumulativeVolume = 0;

    return data.map((item) => {
      const typicalPrice = (item.high + item.low + item.close) / 3;
      cumulativePV += typicalPrice * item.volume;
      cumulativeVolume += item.volume;
      const vwap = cumulativePV / cumulativeVolume;

      return {
        time: item.time,
        value: vwap
      };
    });
  };

  // EMA Calculation Function
  const calculateEMA = (data, period) => {
    const k = 2 / (period + 1);
    let ema = data[0].close;
    
    return data.map((item, index) => {
      if (index === 0) {
        return { time: item.time, value: ema };
      }
      ema = (item.close - ema) * k + ema;
      return { time: item.time, value: ema };
    });
  };

  return <div ref={chartContainerRef} className="ChartContainer" style={{ width: '100%', height: '100%' }} />;
}

export default Chart;
