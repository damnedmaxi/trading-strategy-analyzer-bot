import { apiClient, toNumber } from './client';
import type { Candle, CandleDTO, SymbolDTO, Timeframe } from './types';
import type { UTCTimestamp } from 'lightweight-charts';

export async function fetchSymbols(): Promise<SymbolDTO[]> {
  const { data } = await apiClient.get<SymbolDTO[]>('/api/datafeeds/symbols/');
  return data;
}

export interface FetchCandlesParams {
  symbol: string;
  timeframe: Timeframe;
  limit?: number;
  start?: string;
  end?: string;
}

export async function fetchCandles(params: FetchCandlesParams): Promise<Candle[]> {
  const { data } = await apiClient.get<CandleDTO[]>(
    '/api/datafeeds/candles/',
    { params: { ...params } },
  );

  return data.map((candle) => ({
    time: Math.floor(new Date(candle.timestamp).getTime() / 1000) as UTCTimestamp,
    open: toNumber(candle.open),
    high: toNumber(candle.high),
    low: toNumber(candle.low),
    close: toNumber(candle.close),
    volume: toNumber(candle.volume),
  }));
}
