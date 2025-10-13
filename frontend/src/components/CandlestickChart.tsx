import { useEffect, useMemo, useRef } from 'react';
import { createChart, ColorType, CandlestickSeries, LineSeries } from 'lightweight-charts';
import type {
  CandlestickData,
  ISeriesApi,
  LineData,
  UTCTimestamp,
} from 'lightweight-charts';
import type { Candle, IndicatorPoint, Timeframe } from '../api/types';
import type { StrategyEntry } from '../api/strategy';

interface Props {
  candles: Candle[];
  sma: IndicatorPoint[];
  hma1h: IndicatorPoint[];
  hma4h: IndicatorPoint[];
  entries: StrategyEntry[];
  currentIndex: number;
  timeframe: Timeframe;
}

export function CandlestickChart({ candles, sma, hma1h, hma4h, entries, currentIndex, timeframe }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<ReturnType<typeof createChart> | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const smaSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const hma1hSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const hma4hSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const markerSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);

  const visibleCandles = useMemo(() => {
    if (!candles.length) return [];
    const endIndex = Math.min(currentIndex, candles.length - 1);
    return candles.slice(0, endIndex + 1);
  }, [candles, currentIndex]);

  const visibleSma = useMemo(() => {
    if (!visibleCandles.length) return [];
    const lastTime = visibleCandles[visibleCandles.length - 1].time;
    return sma.filter((point) => point.time <= lastTime);
  }, [sma, visibleCandles]);

  const visibleHma1h = useMemo(() => {
    if (!visibleCandles.length) return [];
    const lastTime = visibleCandles[visibleCandles.length - 1].time;
    return hma1h.filter((point) => point.time <= lastTime);
  }, [hma1h, visibleCandles]);

  const visibleHma4h = useMemo(() => {
    if (!visibleCandles.length) return [];
    const lastTime = visibleCandles[visibleCandles.length - 1].time;
    return hma4h.filter((point) => point.time <= lastTime);
  }, [hma4h, visibleCandles]);

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

    const smaSeries = chart.addSeries(LineSeries, {
      color: '#facc15',
      lineWidth: 2,
      priceLineVisible: false,
      title: 'SMA200',
    });

    const hma1hSeries = chart.addSeries(LineSeries, {
      color: '#60a5fa',
      lineWidth: 2,
      priceLineVisible: false,
      title: 'HMA200 1h',
    });

    const hma4hSeries = chart.addSeries(LineSeries, {
      color: '#a855f7',
      lineWidth: 2,
      priceLineVisible: false,
      title: 'HMA200 4h',
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
    smaSeriesRef.current = smaSeries;
    hma1hSeriesRef.current = hma1hSeries;
    hma4hSeriesRef.current = hma4hSeries;
    markerSeriesRef.current = markerSeries;

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
    if (markerSeriesRef.current) {
      const markerData: LineData<UTCTimestamp>[] = visibleCandles.map((candle) => ({
        time: candle.time,
        value: candle.close,
      }));
      markerSeriesRef.current.setData(markerData);
    }
    chartRef.current.timeScale().fitContent();
    chartRef.current.timeScale().applyOptions({ rightOffset: 6 });
  }, [visibleCandles]);

  useEffect(() => {
    if (!smaSeriesRef.current) return;
    const data: LineData<UTCTimestamp>[] = visibleSma.map((point) => ({
      time: point.time,
      value: point.value,
    }));
    smaSeriesRef.current.setData(data);
  }, [visibleSma]);

  useEffect(() => {
    if (!hma1hSeriesRef.current) return;
    const data: LineData<UTCTimestamp>[] = visibleHma1h.map((point) => ({
      time: point.time,
      value: point.value,
    }));
    hma1hSeriesRef.current.setData(data);
  }, [visibleHma1h]);

  useEffect(() => {
    if (!hma4hSeriesRef.current) return;
    const data: LineData<UTCTimestamp>[] = visibleHma4h.map((point) => ({
      time: point.time,
      value: point.value,
    }));
    hma4hSeriesRef.current.setData(data);
  }, [visibleHma4h]);

  useEffect(() => {
    if (!markerSeriesRef.current) return;
    type Marker = {
      time: UTCTimestamp;
      position: 'belowBar' | 'aboveBar';
      color: string;
      shape: 'arrowUp' | 'arrowDown';
      text: string;
    };

    const markers: Marker[] = entries.map((entry) => ({
      time: entry.time,
      position: entry.direction === 'long' ? 'belowBar' : 'aboveBar',
      color: entry.direction === 'long' ? '#22c55e' : '#ef4444',
      shape: entry.direction === 'long' ? 'arrowUp' : 'arrowDown',
      text: entry.direction === 'long' ? 'LONG' : 'SHORT',
    }));
    const seriesWithMarkers = markerSeriesRef.current as unknown as {
      setMarkers?: (markers: Marker[]) => void;
    };
    if (typeof seriesWithMarkers.setMarkers === 'function') {
      seriesWithMarkers.setMarkers(markers);
    }
  }, [entries]);

  return (
    <div className="chart-wrapper">
      <div ref={containerRef} className="chart-container" />
      <div className="chart-legend">
        <span>{`Timeframe: ${timeframe}`}</span>
        <span>{`Candles: ${visibleCandles.length}`}</span>
      </div>
    </div>
  );
}
