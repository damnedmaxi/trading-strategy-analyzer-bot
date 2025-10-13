import type { UTCTimestamp } from 'lightweight-charts';

export interface SymbolDTO {
  id: number;
  code: string;
  ccxt_symbol: string;
  base_asset: string;
  quote_asset: string;
  exchange: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CandleDTO {
  id: number;
  symbol: SymbolDTO;
  timeframe: string;
  timestamp: string;
  open: string;
  high: string;
  low: string;
  close: string;
  volume: string;
  source: string;
}

export interface Candle {
  time: UTCTimestamp;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface IndicatorPoint {
  time: UTCTimestamp;
  value: number;
}

export type Timeframe = '5m' | '30m' | '1h' | '4h' | '1d';
