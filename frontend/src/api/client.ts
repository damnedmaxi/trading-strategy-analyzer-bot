import axios from 'axios';

const apiBase = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

export const apiClient = axios.create({
  baseURL: apiBase.replace(/\/$/, ''),
  timeout: 15000,
});

export function toNumber(value: string | number): number {
  if (typeof value === 'number') return value;
  return Number(value);
}
