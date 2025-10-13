import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import './App.css';
import { fetchSymbols } from './api/datafeeds';
import type { SymbolDTO, Timeframe } from './api/types';
import { fetchHMASMAStrategy } from './api/strategy';
import { CandlestickChart } from './components/CandlestickChart';
import { usePlayback } from './hooks/usePlayback';

const TIMEFRAMES: Timeframe[] = ['5m', '30m', '1h', '4h', '1d'];

const SPEED_OPTIONS = [100, 250, 500, 1000, 2000];

function App() {
  const symbolsQuery = useQuery<SymbolDTO[]>({
    queryKey: ['symbols'],
    queryFn: fetchSymbols,
    staleTime: 5 * 60 * 1000,
  });

  const [selectedSymbol, setSelectedSymbol] = useState<string>('BTCUSDT');
  const [timeframe, setTimeframe] = useState<Timeframe>('5m');
  const [limit, setLimit] = useState<number>(500);
  const [start, setStart] = useState<string>('');
  const [end, setEnd] = useState<string>('');

  useEffect(() => {
    if (!symbolsQuery.data || !symbolsQuery.data.length) return;
    const exists = symbolsQuery.data.find((symbol) => symbol.code === selectedSymbol);
    if (!exists) {
      setSelectedSymbol(symbolsQuery.data[0].code);
    }
  }, [symbolsQuery.data, selectedSymbol]);

  const strategyQuery = useQuery({
    queryKey: ['hma-sma', selectedSymbol, timeframe, limit, start, end],
    queryFn: () =>
      fetchHMASMAStrategy({
        symbol: selectedSymbol,
        timeframe,
        limit,
        start: start ? `${start}T00:00:00Z` : undefined,
        end: end ? `${end}T23:59:59Z` : undefined,
      }),
    enabled: Boolean(selectedSymbol),
    refetchOnWindowFocus: false,
  });

  const candles = strategyQuery.data?.candles ?? [];
  const sma200 = strategyQuery.data?.sma200 ?? [];
  const hma1h = strategyQuery.data?.hma200?.['1h'] ?? [];
  const hma4h = strategyQuery.data?.hma200?.['4h'] ?? [];
  const entries = strategyQuery.data?.entries ?? [];
  const signalTimeline = strategyQuery.data?.signal_timeline ?? [];
  const effectiveTimeframe = strategyQuery.data?.timeframe ?? timeframe;

  const {
    index,
    isPlaying,
    speed,
    setSpeed,
    toggle,
    stepBackward,
    stepForward,
    goToStart,
    goToEnd,
    setIndex,
  } = usePlayback(candles.length, 500);

  const currentCandle = candles[index] ?? null;
  const currentSignal = useMemo(() => {
    if (!currentCandle || !signalTimeline.length) return null;
    const targetTime = currentCandle.time;
    const reversed = [...signalTimeline].reverse();
    return reversed.find((snapshot) => snapshot.time <= targetTime) ?? signalTimeline[0];
  }, [signalTimeline, currentCandle]);


  return (
    <div className="app">
      <header className="app-header">
        <h1>Strategy Visualizer</h1>
        <p>Reproduce SMA/HMA signals with live playback.</p>
      </header>

      <section className="controls">
        <div className="control-group">
          <label htmlFor="symbol">Symbol</label>
          <select
            id="symbol"
            value={selectedSymbol}
            onChange={(event) => setSelectedSymbol(event.target.value)}
          >
            {symbolsQuery.data?.map((symbol) => (
              <option key={symbol.id} value={symbol.code}>
                {symbol.code}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="timeframe">Timeframe</label>
          <select
            id="timeframe"
            value={timeframe}
            onChange={(event) => setTimeframe(event.target.value as Timeframe)}
          >
            {TIMEFRAMES.map((frame) => (
              <option key={frame} value={frame}>
                {frame}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="limit">Limit</label>
          <input
            id="limit"
            type="number"
            min={100}
            max={2000}
            step={50}
            value={limit}
            onChange={(event) => setLimit(Number(event.target.value) || 500)}
          />
        </div>

        <div className="control-group">
          <label htmlFor="start">Start</label>
          <input
            id="start"
            type="date"
            value={start}
            onChange={(event) => setStart(event.target.value)}
          />
        </div>

        <div className="control-group">
          <label htmlFor="end">End</label>
          <input
            id="end"
            type="date"
            value={end}
            onChange={(event) => setEnd(event.target.value)}
          />
        </div>

        <button
          type="button"
          className="reload"
          onClick={() => strategyQuery.refetch()}
          disabled={strategyQuery.isFetching}
        >
          {strategyQuery.isFetching ? 'Loading…' : 'Reload data'}
        </button>
      </section>

      <main className="content">
        {strategyQuery.isError && (
          <div className="error">
            Failed to load data. Please check the backend connection.
          </div>
        )}

        <div className="chart-section">
          <CandlestickChart
            candles={candles}
            sma={sma200}
            hma1h={hma1h}
            hma4h={hma4h}
            entries={entries}
            currentIndex={index}
            timeframe={effectiveTimeframe}
          />
          <div className="chart-info">
            {currentCandle ? (
              <>
                <div>
                  <strong>Time:</strong>{' '}
                  {format(new Date(currentCandle.time * 1000), 'yyyy-MM-dd HH:mm')}
                </div>
                <div>
                  <strong>Open:</strong> {currentCandle.open.toFixed(2)}{' '}
                  <strong>High:</strong> {currentCandle.high.toFixed(2)}{' '}
                  <strong>Low:</strong> {currentCandle.low.toFixed(2)}{' '}
                  <strong>Close:</strong> {currentCandle.close.toFixed(2)}
                </div>
              </>
            ) : (
              <span>No candle data available.</span>
            )}
            <div>
              <strong>Signal:</strong>{' '}
              {currentSignal
                ? currentSignal.should_enter_long
                  ? 'LONG READY'
                  : currentSignal.should_enter_short
                  ? 'SHORT READY'
                  : 'No entry'
                : 'No entry'}
            </div>
          </div>
        </div>

        <div className="playback">
          <div className="playback-buttons">
            <button type="button" onClick={goToStart} disabled={!candles.length}>
              ⏮
            </button>
            <button type="button" onClick={stepBackward} disabled={!candles.length}>
              ◀
            </button>
            <button
              type="button"
              className="primary"
              onClick={toggle}
              disabled={!candles.length}
            >
              {isPlaying ? 'Pause' : 'Play'}
            </button>
            <button type="button" onClick={stepForward} disabled={!candles.length}>
              ▶
            </button>
            <button type="button" onClick={goToEnd} disabled={!candles.length}>
              ⏭
            </button>
          </div>
          <div className="playback-speed">
            <label htmlFor="speed">Speed</label>
            <select
              id="speed"
              value={speed}
              onChange={(event) => setSpeed(Number(event.target.value))}
            >
              {SPEED_OPTIONS.map((value) => (
                <option key={value} value={value}>
                  {`${value} ms`}
                </option>
              ))}
            </select>
          </div>
          <div className="playback-progress">
            <input
              type="range"
              min={0}
              max={Math.max(candles.length - 1, 0)}
              value={index}
              onChange={(event) => setIndex(Number(event.target.value))}
              disabled={!candles.length}
            />
            <span>
              {candles.length ? `${index + 1} / ${candles.length}` : '0 / 0'}
            </span>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
