import { Request, Response } from 'express';
import * as metricsService from '../services/metrics.service.js';

const validPeriods = ['1h', '2h', '3h', '4h', '8h', '24h', '3d', '7d', '30d', 'all'];

export class MetricsController {
  async getSystemMetrics(req: Request, res: Response): Promise<void> {
    try {
      const period = (req.query.period as string) || 'all';

      if (!validPeriods.includes(period)) {
        res.status(400).json({
          error: 'Invalid period',
          valid_periods: validPeriods
        });
        return;
      }

      const metrics = await metricsService.getSystemMetrics(period);

      res.json({
        total_requests: metrics.totalRequests,
        tokens_used: metrics.tokensUsed,
        avg_latency_ms: metrics.avgLatencyMs,
        success_rate: metrics.successRate,
        period: metrics.period,
        timestamp: new Date().toISOString(),
      });
    } catch (error) {
      console.error('Error getting metrics:', error);
      res.status(500).json({ error: 'Failed to get metrics' });
    }
  }

  async getRateLimitMetrics(req: Request, res: Response): Promise<void> {
    try {
      const period = (req.query.period as string) || 'all';

      if (!validPeriods.includes(period)) {
        res.status(400).json({
          error: 'Invalid period',
          valid_periods: validPeriods
        });
        return;
      }

      const metrics = await metricsService.getRateLimitMetrics(period);

      res.json({
        total_429: metrics.total429,
        user_key_429: metrics.userKey429,
        friend_key_429: metrics.friendKey429,
        period: metrics.period,
        timestamp: new Date().toISOString(),
      });
    } catch (error) {
      console.error('Error getting rate limit metrics:', error);
      res.status(500).json({ error: 'Failed to get rate limit metrics' });
    }
  }
}

export const metricsController = new MetricsController();
