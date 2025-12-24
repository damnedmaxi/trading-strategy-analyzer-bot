import { useEffect, useMemo, useRef, useState } from 'react';
import { createChart, ColorType, CandlestickSeries, LineSeries } from 'lightweight-charts';
import type {
  CandlestickData,
  ISeriesApi,
  LineData,
  UTCTimestamp,
} from 'lightweight-charts';
import type { Candle, Timeframe, Divergence } from '../api/types';
import type { StrategyEntry } from '../api/strategy';
import { fetchDivergences } from '../api/divergences';

export interface IndicatorSeries {
  id: string;
  type: 'sma' | 'hma';
  timeframe: string;
  label: string;
  color: string;
  width?: number;
  data: { time: UTCTimestamp; value: number }[];
}

interface Props {
  candles: Candle[];
  indicatorSeries: IndicatorSeries[];
  entries: StrategyEntry[];
  currentIndex: number;
  timeframe: Timeframe;
  symbol: string;
}

export function CandlestickChart({ candles, indicatorSeries, entries, currentIndex, timeframe, symbol }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<ReturnType<typeof createChart> | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const markerSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const indicatorSeriesRefs = useRef<Map<string, ISeriesApi<'Line'>>>(new Map());
  
  // Divergence state
  const [showDivergences, setShowDivergences] = useState(false);
  const [showAllTimeframes, setShowAllTimeframes] = useState(false);
  const [divergences, setDivergences] = useState<Divergence[]>([]);
  const divergenceSeriesRefs = useRef<Map<string, ISeriesApi<'Line'>>>(new Map());

  const visibleCandles = useMemo(() => {
    if (!candles.length) return [];
    const endIndex = Math.min(currentIndex, candles.length - 1);
    return candles.slice(0, endIndex + 1);
  }, [candles, currentIndex]);

  // Load divergences when settings change
  useEffect(() => {
    if (!showDivergences || !visibleCandles.length) {
      setDivergences([]);
      return;
    }

    const loadDivergences = async () => {
      try {
        const startTime = new Date(visibleCandles[0].time * 1000).toISOString();
        const endTime = new Date(visibleCandles[visibleCandles.length - 1].time * 1000).toISOString();
        
        const fetchedDivergences = await fetchDivergences(
          symbol,
          timeframe,
          startTime,
          endTime,
          showAllTimeframes
        );
        
        setDivergences(fetchedDivergences);
      } catch (error) {
        console.error('Error loading divergences:', error);
        setDivergences([]);
      }
    };

    loadDivergences();
  }, [showDivergences, showAllTimeframes, visibleCandles, symbol, timeframe]);

  useEffect(() => {
    if (!containerRef.current) return () => undefined;

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#0b1120' },
        textColor: '#cbd5f5',
      },
      rightPriceScale: {
        borderVisible: false,
      },
      timeScale: {
        borderVisible: false,
        timeVisible: true,
        secondsVisible: false,
      },
      localization: {
        // Use browser's local timezone
        timeFormatter: (timestamp: number) => {
          const date = new Date(timestamp * 1000);
          const year = date.getFullYear();
          const month = String(date.getMonth() + 1).padStart(2, '0');
          const day = String(date.getDate()).padStart(2, '0');
          const hour = String(date.getHours()).padStart(2, '0');
          const minute = String(date.getMinutes()).padStart(2, '0');
          const second = String(date.getSeconds()).padStart(2, '0');
          return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
        },
      },
      crosshair: {
        mode: 0,
      },
      grid: {
        vertLines: { color: '#1f2937' },
        horzLines: { color: '#1f2937' },
      },
    });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#22c55e',
      downColor: '#ef4444',
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
      borderVisible: false,
    });

    const markerSeries = chart.addSeries(LineSeries, {
      color: 'rgba(0,0,0,0)',
      lineWidth: 1,
      priceLineVisible: false,
      crosshairMarkerVisible: false,
      lastValueVisible: false,
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    markerSeriesRef.current = markerSeries;
    indicatorSeriesRefs.current.clear();

    // Clear divergence series refs
    divergenceSeriesRefs.current.clear();

    const resize = () => {
      if (!containerRef.current || !chartRef.current) return;
      const { clientWidth, clientHeight } = containerRef.current;
      chartRef.current.applyOptions({ width: clientWidth, height: clientHeight });
    };
    resize();
    window.addEventListener('resize', resize);

    return () => {
      window.removeEventListener('resize', resize);
      chart.remove();
    };
  }, []);

  useEffect(() => {
    if (!chartRef.current || !candleSeriesRef.current) return;
    const seriesData: CandlestickData<UTCTimestamp>[] = visibleCandles.map((candle) => ({
      time: candle.time,
      open: candle.open,
      high: candle.high,
      low: candle.low,
      close: candle.close,
    }));
    candleSeriesRef.current.setData(seriesData);
    chartRef.current.timeScale().fitContent();
    chartRef.current.timeScale().applyOptions({ rightOffset: 6 });
  }, [visibleCandles]);

  // Update marker series data to include both candle times and entry sourceTimes
  // This ensures markers can be placed at any sourceTime
  useEffect(() => {
    if (!markerSeriesRef.current || !visibleCandles.length) return;
    
    // Create a map of all timestamps to their prices
    const timeToPrice = new Map<UTCTimestamp, number>();
    
    // Add candle timestamps
    visibleCandles.forEach((candle) => {
      timeToPrice.set(candle.time, candle.close);
    });
    
    // Add entry sourceTimes with prices
    entries.forEach((entry) => {
      if (!timeToPrice.has(entry.sourceTime)) {
        // Use entry.price if available, otherwise find nearest candle
        let price = entry.price;
        if (price == null) {
          // Find the closest candle by timestamp
          let minDiff = Infinity;
          let closestPrice = visibleCandles[0]?.close ?? 0;
          for (const candle of visibleCandles) {
            const diff = Math.abs(candle.time - entry.sourceTime);
            if (diff < minDiff) {
              minDiff = diff;
              closestPrice = candle.close;
            }
          }
          price = closestPrice;
        }
        timeToPrice.set(entry.sourceTime, price);
      }
    });
    
    // Convert to sorted array
    const markerData: LineData<UTCTimestamp>[] = Array.from(timeToPrice.entries())
      .sort((a, b) => a[0] - b[0])
      .map(([time, value]) => ({ time, value }));
    
    markerSeriesRef.current.setData(markerData);
  }, [visibleCandles, entries]);

  useEffect(() => {
    if (!chartRef.current) return;
    const map = indicatorSeriesRefs.current;
    const cutoff = visibleCandles.length ? visibleCandles[visibleCandles.length - 1].time : null;
    const activeIds = new Set(indicatorSeries.map((series) => series.id));

    Array.from(map.entries()).forEach(([id, lineSeries]) => {
      if (!activeIds.has(id)) {
        chartRef.current?.removeSeries(lineSeries);
        map.delete(id);
      }
    });

    indicatorSeries.forEach((series) => {
      let lineSeries = map.get(series.id);
      if (!lineSeries) {
        lineSeries = chartRef.current!.addSeries(LineSeries, {
          color: series.color,
          lineWidth: series.width ?? 2,
          priceLineVisible: false,
          title: series.label,
        });
        map.set(series.id, lineSeries);
      } else {
        // Update style if it changed
        lineSeries.applyOptions({
          color: series.color,
          lineWidth: series.width ?? 2,
          priceLineVisible: false,
          title: series.label,
        });
      }
      const data = cutoff == null ? series.data : series.data.filter((point) => point.time <= cutoff);
      lineSeries.setData(data);
    });
  }, [indicatorSeries, visibleCandles]);

  useEffect(() => {
    if (!markerSeriesRef.current) return;
    type Marker = {
      time: UTCTimestamp;
      position: 'belowBar' | 'aboveBar';
      color: string;
      shape: 'arrowUp' | 'arrowDown';
      text: string;
    };

    const markers: Marker[] = entries.map((entry) => {
      switch (entry.direction) {
        case 'long':
          return {
            time: entry.sourceTime,
            position: 'belowBar',
            color: '#22c55e',
            shape: 'arrowUp',
            text: 'LONG',
          };
        case 'short':
          return {
            time: entry.sourceTime,
            position: 'aboveBar',
            color: '#ef4444',
            shape: 'arrowDown',
            text: 'SHORT',
          };
        case 'long_exit':
          return {
            time: entry.sourceTime,
            position: 'aboveBar',
            color: '#f59e0b',
            shape: 'arrowDown',
            text: 'LONG EXIT',
          };
        case 'short_exit':
          return {
            time: entry.sourceTime,
            position: 'belowBar',
            color: '#0ea5e9',
            shape: 'arrowUp',
            text: 'SHORT EXIT',
          };
        default:
          return {
            time: entry.sourceTime,
            position: 'belowBar',
            color: '#6b7280',
            shape: 'arrowUp',
            text: entry.direction,
          };
      }
    });
    const seriesWithMarkers = markerSeriesRef.current as unknown as {
      setMarkers?: (markers: Marker[]) => void;
    };
    if (typeof seriesWithMarkers.setMarkers === 'function') {
      seriesWithMarkers.setMarkers(markers);
    }
  }, [entries]);

  // Draw divergences
  useEffect(() => {
    if (!chartRef.current || !showDivergences || !divergences.length) {
      // Remove all divergence series if not showing
      divergenceSeriesRefs.current.forEach((series) => {
        chartRef.current?.removeSeries(series);
      });
      divergenceSeriesRefs.current.clear();
      return;
    }

    // Get color mapping for divergence types
    const getDivergenceColor = (type: Divergence['type']): string => {
      switch (type) {
        case 'macd_bullish':
          return '#22c55e'; // Green
        case 'macd_bearish':
          return '#ef4444'; // Red
        case 'rsi_bullish':
          return '#3b82f6'; // Blue
        case 'rsi_bearish':
          return '#f59e0b'; // Orange
        default:
          return '#6b7280'; // Gray
      }
    };

    // Create or update divergence series
    divergences.forEach((divergence) => {
      const seriesKey = `${divergence.type}_${divergence.id}`;
      
      if (!divergenceSeriesRefs.current.has(seriesKey)) {
        // Create new series for this divergence
        const series = chartRef.current!.addSeries(LineSeries, {
          color: getDivergenceColor(divergence.type),
          lineWidth: 2,
          priceLineVisible: false,
          crosshairMarkerVisible: false,
          lastValueVisible: false,
          title: `${divergence.type.toUpperCase()} (${divergence.timeframe})`,
        });
        
        divergenceSeriesRefs.current.set(seriesKey, series);
      }
      
      const series = divergenceSeriesRefs.current.get(seriesKey)!;
      
      // Set the line data (start and end points)
      const lineData: LineData<UTCTimestamp>[] = [
        {
          time: divergence.startTime,
          value: divergence.startPrice,
        },
        {
          time: divergence.endTime,
          value: divergence.endPrice,
        },
      ];
      
      series.setData(lineData);
    });

    // Remove series for divergences that are no longer present
    const currentSeriesKeys = new Set(
      divergences.map((d) => `${d.type}_${d.id}`)
    );
    
    divergenceSeriesRefs.current.forEach((series, key) => {
      if (!currentSeriesKeys.has(key)) {
        chartRef.current?.removeSeries(series);
        divergenceSeriesRefs.current.delete(key);
      }
    });
  }, [divergences, showDivergences]);

  return (
    <div className="chart-wrapper">
      <div className="chart-controls">
        <label className="control-item">
          <input
            type="checkbox"
            checked={showDivergences}
            onChange={(e) => setShowDivergences(e.target.checked)}
          />
          Show Divergences
        </label>
        {showDivergences && (
          <label className="control-item">
            <input
              type="checkbox"
              checked={showAllTimeframes}
              onChange={(e) => setShowAllTimeframes(e.target.checked)}
            />
            All Timeframes
          </label>
        )}
      </div>
      <div ref={containerRef} className="chart-container" />
      <div className="chart-legend">
        <span>{`Timeframe: ${timeframe}`}</span>
        <span>{`Candles: ${visibleCandles.length}`}</span>
        {showDivergences && (
          <span>{`Divergences: ${divergences.length}`}</span>
        )}
      </div>
    </div>
  );
}
