import type { Candle, IndicatorPoint } from '../api/types';

export function calculateSMA(candles: Candle[], period: number): IndicatorPoint[] {
  const result: IndicatorPoint[] = [];
  if (period <= 0) return result;

  let sum = 0;
  for (let i = 0; i < candles.length; i += 1) {
    sum += candles[i].close;
    if (i >= period) {
      sum -= candles[i - period].close;
    }
    if (i >= period - 1) {
      result.push({
        time: candles[i].time,
        value: sum / period,
      });
    }
  }
  return result;
}

function weightedMovingAverage(values: number[], period: number): number[] {
  const result: number[] = [];
  if (period <= 0) return result;
  const weights = Array.from({ length: period }, (_, idx) => idx + 1);
  const weightSum = weights.reduce((acc, weight) => acc + weight, 0);

  for (let i = 0; i < values.length; i += 1) {
    if (i + 1 < period) {
      result.push(NaN);
      continue;
    }
    let acc = 0;
    for (let j = 0; j < period; j += 1) {
      const value = values[i - j];
      const weight = weights[j];
      acc += value * weight;
    }
    result.push(acc / weightSum);
  }

  return result;
}

export function calculateHMA(candles: Candle[], period: number): IndicatorPoint[] {
  const result: IndicatorPoint[] = [];
  if (period <= 0) return result;

  const closes = candles.map((candle) => candle.close);
  const periodHalf = Math.max(1, Math.floor(period / 2));
  const periodSqrt = Math.max(1, Math.floor(Math.sqrt(period)));

  const wmaHalf = weightedMovingAverage(closes, periodHalf);
  const wmaFull = weightedMovingAverage(closes, period);

  const hullInput: number[] = closes.map((_, idx) => {
    const half = wmaHalf[idx];
    const full = wmaFull[idx];
    if (Number.isNaN(half) || Number.isNaN(full)) return NaN;
    return 2 * half - full;
  });

  const hull = weightedMovingAverage(hullInput, periodSqrt);

  for (let i = 0; i < candles.length; i += 1) {
    const value = hull[i];
    if (!Number.isNaN(value)) {
      result.push({
        time: candles[i].time,
        value,
      });
    }
  }

  return result;
}
