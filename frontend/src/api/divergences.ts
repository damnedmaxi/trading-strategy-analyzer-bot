import type { DivergenceDTO, Divergence, Timeframe } from './types';
import { apiClient } from './client';

export async function fetchDivergences(
  symbol: string,
  timeframe: Timeframe,
  startTime?: string,
  endTime?: string,
  showAllTimeframes: boolean = false
): Promise<Divergence[]> {
  const params = new URLSearchParams({
    symbol,
    timeframe,
    show_all_timeframes: showAllTimeframes.toString(),
  });

  if (startTime) {
    params.append('start', startTime);
  }
  if (endTime) {
    params.append('end', endTime);
  }

  const response = await apiClient.get<DivergenceDTO[]>(`/api/datafeeds/divergences/?${params}`);
  
  return response.data.map(transformDivergenceDTO);
}

function transformDivergenceDTO(dto: DivergenceDTO): Divergence {
  return {
    id: dto.id,
    timeframe: dto.timeframe as Timeframe,
    type: dto.divergence_type,
    startTime: Math.floor(new Date(dto.start_timestamp).getTime() / 1000) as any,
    startPrice: parseFloat(dto.start_price),
    endTime: Math.floor(new Date(dto.end_timestamp).getTime() / 1000) as any,
    endPrice: parseFloat(dto.end_price),
    isBullish: dto.is_bullish,
    isMacd: dto.is_macd,
  };
}
