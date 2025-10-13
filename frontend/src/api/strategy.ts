import type { UTCTimestamp } from 'lightweight-charts';

import { apiClient, toNumber } from './client';
import type { IndicatorPoint, Timeframe } from './types';
import type { Candle } from './types';

export interface StrategyEntry {
  time: UTCTimestamp;
  sourceTime: UTCTimestamp;
  direction: 'long' | 'short';
}

export interface SignalSnapshot {
  time: UTCTimestamp;
  should_enter: boolean;
  should_enter_long: boolean;
  should_enter_short: boolean;
}

export interface HMASMAStrategyResponse {
  symbol: string;
  timeframe: Timeframe;
  candles: Candle[];
  sma200: IndicatorPoint[];
  hma200: Record<string, IndicatorPoint[]>;
  entries: StrategyEntry[];
  signal_timeline: SignalSnapshot[];
  latest_signal: StrategySnapshot | null;
}

export interface StrategySnapshot {
  time: string;
  should_enter: boolean;
  should_enter_long: boolean;
  should_enter_short: boolean;
  breakdown: Record<TimeframeKey, BreakdownEntry>;
}

type TimeframeKey = '5m' | '1h' | '4h';

interface BreakdownEntry {
  price: number | null;
  indicator: number | null;
  condition_long: boolean;
  condition_short: boolean;
  condition_met: boolean;
}

export interface StrategyRunParams {
  symbol: string;
  timeframe: Timeframe;
  limit?: number;
  start?: string;
  end?: string;
}

export async function fetchHMASMAStrategy(params: StrategyRunParams): Promise<HMASMAStrategyResponse> {
  const { data } = await apiClient.get('/api/strategies/hma-sma/run/', {
    params,
  });

  return {
    symbol: data.symbol,
    timeframe: data.timeframe,
    candles: data.candles.map((c: any) => ({
      time: Math.floor(new Date(c.time).getTime() / 1000) as UTCTimestamp,
      open: toNumber(c.open),
      high: toNumber(c.high),
      low: toNumber(c.low),
      close: toNumber(c.close),
      volume: toNumber(c.volume),
    })),
    sma200: convertIndicator(data.sma200),
    hma200: Object.fromEntries(
      Object.entries(data.hma200 || {}).map(([key, series]) => [key, convertIndicator(series as any)]),
    ),
    entries: (data.entries || []).map((entry: any) => ({
      time: Math.floor(new Date(entry.time).getTime() / 1000) as UTCTimestamp,
      sourceTime: Math.floor(new Date((entry.source_time ?? entry.time)).getTime() / 1000) as UTCTimestamp,
      direction: entry.direction,
    })),
    signal_timeline: (data.signal_timeline || []).map((snapshot: any) => ({
      time: Math.floor(new Date(snapshot.time).getTime() / 1000) as UTCTimestamp,
      should_enter: Boolean(snapshot.should_enter),
      should_enter_long: Boolean(snapshot.should_enter_long ?? snapshot.should_enter),
      should_enter_short: Boolean(snapshot.should_enter_short ?? false),
    })),
    latest_signal: data.latest_signal ? convertSnapshot(data.latest_signal) : null,
  };
}

function convertIndicator(series: any[]): IndicatorPoint[] {
  return (series || []).map((point) => ({
    time: Math.floor(new Date(point.time).getTime() / 1000) as UTCTimestamp,
    value: toNumber(point.value),
  }));
}

function convertSnapshot(snapshot: any): StrategySnapshot {
  const breakdownEntries: Record<TimeframeKey, BreakdownEntry> = {
    '5m': convertBreakdownEntry(snapshot.breakdown?.['5m']),
    '1h': convertBreakdownEntry(snapshot.breakdown?.['1h']),
    '4h': convertBreakdownEntry(snapshot.breakdown?.['4h']),
  };
  return {
    time: snapshot.time,
    should_enter: Boolean(snapshot.should_enter),
    should_enter_long: Boolean(snapshot.should_enter_long ?? snapshot.should_enter),
    should_enter_short: Boolean(snapshot.should_enter_short ?? false),
    breakdown: breakdownEntries,
  };
}

function convertBreakdownEntry(entry: any): BreakdownEntry {
  if (!entry) {
    return {
      price: null,
      indicator: null,
      condition_long: false,
      condition_short: false,
      condition_met: false,
    };
  }
  return {
    price: entry.price != null ? Number(entry.price) : null,
    indicator: entry.indicator != null ? Number(entry.indicator) : null,
    condition_long: Boolean(entry.condition_long ?? entry.condition_met ?? false),
    condition_short: Boolean(entry.condition_short ?? false),
    condition_met: Boolean(entry.condition_met ?? entry.condition_long ?? false),
  };
}
