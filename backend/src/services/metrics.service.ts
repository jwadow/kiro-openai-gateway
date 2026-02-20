import { requestLogRepository } from '../repositories/request-log.repository.js';

export interface SystemMetrics {
  totalRequests: number;
  tokensUsed: number;
  avgLatencyMs: number;
  successRate: number;
  period: string;
}

export interface RateLimitMetrics {
  total429: number;
  userKey429: number;
  friendKey429: number;
  period: string;
}

function getPeriodSince(period: string): Date | undefined {
  switch (period) {
    case '1h':
      return new Date(Date.now() - 60 * 60 * 1000);
    case '2h':
      return new Date(Date.now() - 2 * 60 * 60 * 1000);
    case '3h':
      return new Date(Date.now() - 3 * 60 * 60 * 1000);
    case '4h':
      return new Date(Date.now() - 4 * 60 * 60 * 1000);
    case '8h':
      return new Date(Date.now() - 8 * 60 * 60 * 1000);
    case '24h':
      return new Date(Date.now() - 24 * 60 * 60 * 1000);
    case '3d':
      return new Date(Date.now() - 3 * 24 * 60 * 60 * 1000);
    case '7d':
      return new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
    case '30d':
      return new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
    case 'all':
    default:
      return undefined;
  }
}

export async function getSystemMetrics(period: string = 'all'): Promise<SystemMetrics> {
  const since = getPeriodSince(period);
  const metrics = await requestLogRepository.getMetrics(since);

  return {
    ...metrics,
    period,
  };
}

export async function getRateLimitMetrics(period: string = 'all'): Promise<RateLimitMetrics> {
  const since = getPeriodSince(period);
  const metrics = await requestLogRepository.getRateLimitMetrics(since);

  return {
    ...metrics,
    period,
  };
}
