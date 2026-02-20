import { Router, Request, Response } from 'express';
import { z } from 'zod';
import * as userKeyService from '../services/userkey.service.js';
import * as metricsService from '../services/metrics.service.js';
import { expirationSchedulerService } from '../services/expiration-scheduler.service.js';
import { creditsResetLogRepository } from '../repositories/credits-reset-log.repository.js';

const router = Router();

// Validation schemas
// Note: tier removed from createKeySchema as part of tier system deprecation (Story 3.2)
const createKeySchema = z.object({
  name: z.string().min(1).max(100),
  notes: z.string().max(500).optional(),
});

const updateKeySchema = z.object({
  notes: z.string().max(500).optional(),
  isActive: z.boolean().optional(),
});

// GET /admin/keys - List all user keys
router.get('/keys', async (_req: Request, res: Response) => {
  try {
    const keys = await userKeyService.listUserKeys();
    const stats = await userKeyService.getKeyStats();

    res.json({
      total: stats.total,
      active: stats.active,
      keys: keys.map(k => ({
        ...k,
        id: k._id,
      })),
    });
  } catch (error) {
    console.error('Error listing keys:', error);
    res.status(500).json({ error: 'Failed to list keys' });
  }
});

// POST /admin/keys - Create new user key
router.post('/keys', async (req: Request, res: Response) => {
  try {
    const input = createKeySchema.parse(req.body);
    const key = await userKeyService.createUserKey(input);

    // Note: tier removed from response as part of tier system deprecation (Story 3.2)
    res.status(201).json({
      id: key._id,
      name: key.name,
      created_at: key.createdAt,
    });
  } catch (error) {
    if (error instanceof z.ZodError) {
      res.status(400).json({ error: 'Invalid input', details: error.errors });
      return;
    }
    console.error('Error creating key:', error);
    res.status(500).json({ error: 'Failed to create key' });
  }
});

// GET /admin/keys/:id - Get single key details
router.get('/keys/:id', async (req: Request, res: Response) => {
  try {
    const key = await userKeyService.getUserKey(req.params.id);
    if (!key) {
      res.status(404).json({ error: 'Key not found' });
      return;
    }

    res.json({
      ...key,
      id: key._id,
    });
  } catch (error) {
    console.error('Error getting key:', error);
    res.status(500).json({ error: 'Failed to get key' });
  }
});

// PATCH /admin/keys/:id - Update user key
router.patch('/keys/:id', async (req: Request, res: Response) => {
  try {
    const input = updateKeySchema.parse(req.body);
    const key = await userKeyService.updateUserKey(req.params.id, input);

    if (!key) {
      res.status(404).json({ error: 'Key not found' });
      return;
    }

    res.json({
      id: key._id,
      is_active: key.isActive,
      updated_at: new Date().toISOString(),
    });
  } catch (error) {
    if (error instanceof z.ZodError) {
      res.status(400).json({ error: 'Invalid input', details: error.errors });
      return;
    }
    console.error('Error updating key:', error);
    res.status(500).json({ error: 'Failed to update key' });
  }
});

// DELETE /admin/keys/:id - Revoke or permanently delete user key
// Use ?permanent=true to permanently delete
router.delete('/keys/:id', async (req: Request, res: Response) => {
  try {
    const permanent = req.query.permanent === 'true';
    
    if (permanent) {
      const key = await userKeyService.deleteUserKey(req.params.id);
      if (!key) {
        res.status(404).json({ error: 'Key not found' });
        return;
      }
      res.json({
        id: key._id,
        deleted: true,
        deleted_at: new Date().toISOString(),
      });
    } else {
      const key = await userKeyService.revokeUserKey(req.params.id);
      if (!key) {
        res.status(404).json({ error: 'Key not found' });
        return;
      }
      res.json({
        id: key._id,
        revoked: true,
        revoked_at: new Date().toISOString(),
      });
    }
  } catch (error) {
    console.error('Error deleting/revoking key:', error);
    res.status(500).json({ error: 'Failed to delete/revoke key' });
  }
});

// POST /admin/keys/:id/reset - Reset usage for a key
router.post('/keys/:id/reset', async (req: Request, res: Response) => {
  try {
    const key = await userKeyService.resetUserKeyUsage(req.params.id);

    if (!key) {
      res.status(404).json({ error: 'Key not found' });
      return;
    }

    res.json({
      id: key._id,
      tokens_used: 0,
      requests_count: 0,
      reset_at: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error resetting key:', error);
    res.status(500).json({ error: 'Failed to reset key' });
  }
});

// GET /admin/metrics - Get system-wide metrics
router.get('/metrics', async (req: Request, res: Response) => {
  try {
    const period = (req.query.period as string) || 'all';
    const validPeriods = ['1h', '2h', '3h', '4h', '8h', '24h', '3d', '7d', '30d', 'all'];

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
});

// GET /admin/metrics/rate-limit - Get rate limit metrics (429 responses)
router.get('/metrics/rate-limit', async (req: Request, res: Response) => {
  try {
    const period = (req.query.period as string) || 'all';
    const validPeriods = ['1h', '2h', '3h', '4h', '8h', '24h', '3d', '7d', '30d', 'all'];

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
});

// ==================== EXPIRED CREDITS MANAGEMENT ====================

// GET /admin/expired-credits-stats - Get stats about expired users with credits
router.get('/expired-credits-stats', async (_req: Request, res: Response) => {
  try {
    const expiredUsers = await expirationSchedulerService.findExpiredUsersWithCredits();
    const totalCredits = expiredUsers.reduce((sum, u) => sum + u.credits, 0);

    res.json({
      count: expiredUsers.length,
      totalCredits: Math.round(totalCredits * 100) / 100,
      users: expiredUsers.map(u => ({
        username: u.username,
        credits: Math.round(u.credits * 100) / 100,
        expiresAt: u.expiresAt,
      })),
      scheduledCount: expirationSchedulerService.getScheduledCount(),
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error getting expired credits stats:', error);
    res.status(500).json({ error: 'Failed to get expired credits stats' });
  }
});

// POST /admin/cleanup-expired-credits - Reset all expired users' credits
router.post('/cleanup-expired-credits', async (req: Request, res: Response) => {
  try {
    const dryRun = req.body.dryRun === true;
    const result = await expirationSchedulerService.bulkResetExpired(dryRun);

    res.json({
      dryRun,
      affected: result.affected,
      totalCredits: Math.round(result.totalCredits * 100) / 100,
      users: result.users.map(u => ({
        username: u.username,
        creditsBefore: Math.round(u.creditsBefore * 100) / 100,
      })),
      message: dryRun
        ? `Would reset ${result.affected} users with $${result.totalCredits.toFixed(2)} credits`
        : `Reset ${result.affected} users with $${result.totalCredits.toFixed(2)} credits`,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error cleaning up expired credits:', error);
    res.status(500).json({ error: 'Failed to cleanup expired credits' });
  }
});

// GET /admin/credits-reset-logs - Get credits reset logs
router.get('/credits-reset-logs', async (req: Request, res: Response) => {
  try {
    const username = req.query.username as string | undefined;
    const limit = Math.min(parseInt(req.query.limit as string) || 50, 200);
    const offset = parseInt(req.query.offset as string) || 0;

    let logs;
    let total;

    if (username) {
      logs = await creditsResetLogRepository.findByUsername(username, limit, offset);
      total = await creditsResetLogRepository.countByUsername(username);
    } else {
      logs = await creditsResetLogRepository.findRecent(limit, offset);
      total = await creditsResetLogRepository.countAll();
    }

    res.json({
      logs: logs.map(log => ({
        id: log._id,
        username: log.username,
        creditsBefore: Math.round(log.creditsBefore * 100) / 100,
        expiresAt: log.expiresAt,
        resetAt: log.resetAt,
        resetBy: log.resetBy,
        note: log.note,
      })),
      total,
      limit,
      offset,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error getting credits reset logs:', error);
    res.status(500).json({ error: 'Failed to get credits reset logs' });
  }
});

export default router;
