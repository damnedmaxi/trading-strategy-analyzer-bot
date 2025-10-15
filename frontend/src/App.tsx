import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import type { UTCTimestamp } from 'lightweight-charts';
import './App.css';
import { fetchSymbols } from './api/datafeeds';
import type { SymbolDTO, Timeframe } from './api/types';
import { fetchHMASMAStrategy } from './api/strategy';
import type { StrategyEntry } from './api/strategy';
import { CandlestickChart } from './components/CandlestickChart';
import { usePlayback } from './hooks/usePlayback';

const TIMEFRAMES: Timeframe[] = ['5m', '30m', '1h', '4h', '1d'];

const SPEED_OPTIONS = [100, 250, 500, 1000, 2000];

type OpenPosition = { time: UTCTimestamp; price: number };
type Trade = {
  direction: 'long' | 'short';
  entryTime: UTCTimestamp;
  exitTime: UTCTimestamp;
  entryPrice: number;
  exitPrice: number;
  pnl: number;
};

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
  const [positionSize, setPositionSize] = useState<number>(1000);
  const [strategy, setStrategy] = useState<string>('1');

  useEffect(() => {
    if (!symbolsQuery.data || !symbolsQuery.data.length) return;
    const exists = symbolsQuery.data.find((symbol) => symbol.code === selectedSymbol);
    if (!exists) {
      setSelectedSymbol(symbolsQuery.data[0].code);
    }
  }, [symbolsQuery.data, selectedSymbol]);

  const strategyQuery = useQuery({
    queryKey: ['hma-sma', selectedSymbol, timeframe, limit, start, end, strategy],
    queryFn: () =>
      fetchHMASMAStrategy({
        symbol: selectedSymbol,
        timeframe,
        limit,
        start: start ? `${start}T00:00:00Z` : undefined,
        end: end ? `${end}T23:59:59Z` : undefined,
        strategy,
      }),
    enabled: Boolean(selectedSymbol),
    refetchOnWindowFocus: false,
  });

  const candles = strategyQuery.data?.candles ?? [];
  const sma200 = strategyQuery.data?.sma200 ?? [];
  const hma1h = strategyQuery.data?.hma200?.['1h'] ?? [];
  const hma4h = strategyQuery.data?.hma200?.['4h'] ?? [];
  const entries: StrategyEntry[] = strategyQuery.data?.entries ?? [];
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

  // Use the time of the next candle (or end of current candle) for filtering entries
  // This ensures all entries within the current visible candle are included
  const cutoffTime = useMemo(() => {
    if (!currentCandle) return null;
    const nextCandle = candles[index + 1];
    if (nextCandle) {
      return nextCandle.time;
    }
    // For the last candle, calculate end time based on timeframe
    const timeframeDurations: Record<Timeframe, number> = {
      '5m': 5 * 60,
      '30m': 30 * 60,
      '1h': 60 * 60,
      '4h': 4 * 60 * 60,
      '1d': 24 * 60 * 60,
    };
    const duration = timeframeDurations[effectiveTimeframe] || 5 * 60;
    return (currentCandle.time + duration) as UTCTimestamp;
  }, [currentCandle, candles, index, effectiveTimeframe]);

  const visibleEntries = useMemo(() => {
    if (cutoffTime == null) return [];
    return entries.filter((entry) => entry.sourceTime <= cutoffTime);
  }, [entries, cutoffTime]);

  const currentPrice = currentCandle?.close ?? null;

  const metrics = useMemo<{
    trades: Trade[];
    closedPnl: number;
    unrealizedPnl: number;
    totalPnl: number;
    tradeCount: number;
    openLong: OpenPosition | null;
    openShort: OpenPosition | null;
    currentPosition:
      | { direction: 'long'; entryPrice: number; entryTime: UTCTimestamp }
      | { direction: 'short'; entryPrice: number; entryTime: UTCTimestamp }
      | null;
  }>(() => {
    const sortedEntries = [...visibleEntries].sort((a, b) => a.sourceTime - b.sourceTime);
    let openLongPrice: number | null = null;
    let openLongTime: UTCTimestamp | null = null;
    let openShortPrice: number | null = null;
    let openShortTime: UTCTimestamp | null = null;
    const trades: Trade[] = [];

    sortedEntries.forEach((entry) => {
      const price = entry.price ?? null;
      if (price == null) return;

      if (entry.direction === 'long') {
        openLongPrice = price;
        openLongTime = entry.sourceTime;
      } else if (entry.direction === 'long_exit') {
        if (openLongPrice != null && openLongTime != null) {
          const pnl = ((price - openLongPrice) / openLongPrice) * positionSize;
          trades.push({
            direction: 'long',
            entryTime: openLongTime,
            exitTime: entry.sourceTime,
            entryPrice: openLongPrice,
            exitPrice: price,
            pnl,
          });
          openLongPrice = null;
          openLongTime = null;
        }
      } else if (entry.direction === 'short') {
        openShortPrice = price;
        openShortTime = entry.sourceTime;
      } else if (entry.direction === 'short_exit') {
        if (openShortPrice != null && openShortTime != null) {
          const pnl = ((openShortPrice - price) / openShortPrice) * positionSize;
          trades.push({
            direction: 'short',
            entryTime: openShortTime,
            exitTime: entry.sourceTime,
            entryPrice: openShortPrice,
            exitPrice: price,
            pnl,
          });
          openShortPrice = null;
          openShortTime = null;
        }
      }
    });

    const closedPnl = trades.reduce((sum, trade) => sum + trade.pnl, 0);
    let unrealizedPnl = 0;
    if (currentPrice != null) {
      if (openLongPrice != null) {
        unrealizedPnl += ((currentPrice - openLongPrice) / openLongPrice) * positionSize;
      }
      if (openShortPrice != null) {
        unrealizedPnl += ((openShortPrice - currentPrice) / openShortPrice) * positionSize;
      }
    }

    return {
      trades,
      closedPnl,
      unrealizedPnl,
      totalPnl: closedPnl + unrealizedPnl,
      tradeCount: trades.length,
      openLong: openLongPrice != null && openLongTime != null ? { time: openLongTime, price: openLongPrice } : null,
      openShort: openShortPrice != null && openShortTime != null ? { time: openShortTime, price: openShortPrice } : null,
      currentPosition:
        openLongPrice != null && openLongTime != null
          ? { direction: 'long', entryPrice: openLongPrice, entryTime: openLongTime }
          : openShortPrice != null && openShortTime != null
          ? { direction: 'short', entryPrice: openShortPrice, entryTime: openShortTime }
          : null,
    };
  }, [visibleEntries, positionSize, currentPrice]);


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
          <label htmlFor="strategy">Strategy</label>
          <select
            id="strategy"
            value={strategy}
            onChange={(event) => setStrategy(event.target.value)}
          >
            <option value="1">Strategy 1 - Multi-timeframe</option>
            <option value="2">Strategy 2 - Crossover</option>
            <option value="3">Strategy 3 - Smart Crossover Hybrid</option>
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
            entries={visibleEntries}
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
            <div className="signal-status">
              <strong>Signal:</strong>{' '}
              {currentSignal
                ? currentSignal.should_enter_long
                  ? 'LONG READY'
                  : currentSignal.should_enter_short
                  ? 'SHORT READY'
                  : currentSignal.should_exit_long
                  ? 'LONG EXIT'
                  : currentSignal.should_exit_short
                  ? 'SHORT EXIT'
                  : 'No entry'
                : 'No entry'}
            </div>
          </div>
        </div>

        <div className="playback">
          <div className="playback-config">
            <label htmlFor="positionSize">Position Size (USD)</label>
            <input
              id="positionSize"
              type="number"
              min={0}
              step={100}
              value={positionSize}
              onChange={(event) => setPositionSize(Math.max(0, Number(event.target.value) || 0))}
            />
            <div
              className="pnl-display"
              style={{ color: metrics.totalPnl >= 0 ? '#22c55e' : '#ef4444' }}
            >
              Closed: {metrics.closedPnl.toFixed(2)} · Open: {metrics.unrealizedPnl.toFixed(2)} · Total:{' '}
              {metrics.totalPnl.toFixed(2)} USD · Trades: {metrics.tradeCount}
            </div>
            <div className="position-display">
              <strong>Position:</strong>{' '}
              {metrics.currentPosition
                ? `${metrics.currentPosition.direction.toUpperCase()} @ ${metrics.currentPosition.entryPrice.toFixed(
                    2,
                  )}`
                : 'FLAT'}
            </div>
          </div>
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

        <div className="trades-table">
          <h2>Trade History ({metrics.tradeCount} trades)</h2>
          {metrics.trades.length === 0 ? (
            <p className="no-trades">No completed trades yet</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Entry Time</th>
                  <th>Entry Price</th>
                  <th>Exit Time</th>
                  <th>Exit Price</th>
                  <th>Duration</th>
                  <th>PnL (USD)</th>
                  <th>PnL (%)</th>
                  <th>Result</th>
                </tr>
              </thead>
              <tbody>
                {[...metrics.trades].reverse().map((trade, idx) => {
                  const originalIndex = metrics.trades.length - 1 - idx;
                  const durationSeconds = trade.exitTime - trade.entryTime;
                  const durationMinutes = Math.floor(durationSeconds / 60);
                  const durationHours = Math.floor(durationMinutes / 60);
                  const remainingMinutes = durationMinutes % 60;
                  const durationDisplay = 
                    durationHours > 0 
                      ? `${durationHours}h ${remainingMinutes}m`
                      : `${durationMinutes}m`;
                  const pnlPercent = ((trade.pnl / positionSize) * 100).toFixed(2);
                  const pnlPercentNum = parseFloat(pnlPercent);
                  const isWin = trade.pnl > 0;
                  
                  return (
                    <tr key={originalIndex} className={isWin ? 'win' : 'loss'}>
                      <td className="trade-type">
                        <span className={`badge ${trade.direction}`}>
                          {trade.direction.toUpperCase()}
                        </span>
                      </td>
                      <td>{format(new Date(trade.entryTime * 1000), 'yyyy-MM-dd HH:mm:ss')}</td>
                      <td className="price">{trade.entryPrice.toFixed(2)}</td>
                      <td>{format(new Date(trade.exitTime * 1000), 'yyyy-MM-dd HH:mm:ss')}</td>
                      <td className="price">{trade.exitPrice.toFixed(2)}</td>
                      <td>{durationDisplay}</td>
                      <td className={`pnl ${isWin ? 'positive' : 'negative'}`}>
                        {trade.pnl > 0 ? '+' : ''}{trade.pnl.toFixed(2)}
                      </td>
                      <td className={`pnl ${isWin ? 'positive' : 'negative'}`}>
                        {pnlPercentNum > 0 ? '+' : ''}{pnlPercent}%
                      </td>
                      <td>
                        <span className={`result-badge ${isWin ? 'win' : 'loss'}`}>
                          {isWin ? '✓ Win' : '✗ Loss'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
