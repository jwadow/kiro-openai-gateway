import { Router, Request, Response } from 'express';
import { userKeyController } from '../controllers/user-key.controller.js';
import { metricsController } from '../controllers/metrics.controller.js';
import { allowReadOnly, requireAdmin } from '../middleware/role.middleware.js';
import { userRepository } from '../repositories/user.repository.js';
import { requestLogRepository } from '../repositories/request-log.repository.js';
import { paymentRepository } from '../repositories/payment.repository.js';
import { PaymentStatus } from '../models/payment.model.js';
import { expirationSchedulerService } from '../services/expiration-scheduler.service.js';

const router = Router();

// User Keys - users can read, only admin can write
router.get('/keys', (req, res) => userKeyController.list(req, res));
router.get('/keys/:id', (req, res) => userKeyController.get(req, res));
router.post('/keys', requireAdmin, (req, res) => userKeyController.create(req, res));
router.patch('/keys/:id', requireAdmin, (req, res) => userKeyController.update(req, res));
router.delete('/keys/:id', requireAdmin, (req, res) => userKeyController.delete(req, res));
router.post('/keys/:id/reset', requireAdmin, (req, res) => userKeyController.reset(req, res));

// Metrics - all authenticated users can read
router.get('/metrics', (req, res) => metricsController.getSystemMetrics(req, res));

// User Stats - admin only (for dashboard)
router.get('/user-stats', requireAdmin, async (req: Request, res: Response) => {
  try {
    const period = (req.query.period as string) || 'all';
    const stats = await userRepository.getUserStats(period);
    res.json({
      total_users: stats.total,
      active_users: stats.activeUsers,
      total_credits_used: stats.totalCreditsUsed,
      total_credits: stats.totalCredits,
      total_ref_credits: stats.totalRefCredits,
      total_creditsNew: stats.totalCreditsNew,
      total_creditsNewUsed: stats.totalCreditsNewUsed,
      total_input_tokens: stats.totalInputTokens,
      total_output_tokens: stats.totalOutputTokens,
      period,
    });
  } catch (error) {
    console.error('Failed to get user stats:', error);
    res.status(500).json({ error: 'Failed to get user stats' });
  }
});

// User Management - admin only
router.get('/users', requireAdmin, async (req: Request, res: Response) => {
  try {
    const search = req.query.search as string | undefined;
    const [users, statsData, creditsBurnedMap, lastActivityMap] = await Promise.all([
      userRepository.listUsers(search),
      userRepository.getUserStats(),
      requestLogRepository.getCreditsBurnedByUser(),
      requestLogRepository.getLastActivityByUser(),
    ]);
    const usersWithBurn = users.map((user) => ({
      ...user,
      creditsBurned: creditsBurnedMap[user._id] || 0,
      lastActivity: lastActivityMap[user._id] || null,
    }));
    res.json({
      users: usersWithBurn,
      stats: {
        total: statsData.total,
        activeUsers: statsData.activeUsers,
      }
    });
  } catch (error) {
    console.error('Failed to list users:', error);
    res.status(500).json({ error: 'Failed to list users' });
  }
});

router.get('/users/:username', requireAdmin, async (req: Request, res: Response) => {
  try {
    const user = await userRepository.getFullUser(req.params.username);
    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }
    const { passwordHash, passwordSalt, ...safeUser } = user as any;
    res.json(safeUser);
  } catch (error) {
    console.error('Failed to get user:', error);
    res.status(500).json({ error: 'Failed to get user' });
  }
});

router.patch('/users/:username/credits', requireAdmin, async (req: Request, res: Response) => {
  try {
    const { credits, resetExpiration = true } = req.body;

    if (typeof credits !== 'number' || credits < 0) {
      return res.status(400).json({ error: 'Credits must be a non-negative number' });
    }

    const user = await userRepository.setCredits(req.params.username, credits, resetExpiration);
    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }
    
    res.json({ 
      success: true, 
      message: `Set credits to $${credits} for ${req.params.username}`,
      user: {
        username: user._id,
        credits: user.credits,
        expiresAt: user.expiresAt,
      }
    });
  } catch (error) {
    console.error('Failed to update user credits:', error);
    res.status(500).json({ error: 'Failed to update user credits' });
  }
});

router.patch('/users/:username/refCredits', requireAdmin, async (req: Request, res: Response) => {
  try {
    const { refCredits } = req.body;

    if (typeof refCredits !== 'number' || refCredits < 0) {
      return res.status(400).json({ error: 'RefCredits must be a non-negative number' });
    }

    const user = await userRepository.updateRefCredits(req.params.username, refCredits);
    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    res.json({
      success: true,
      message: `Updated ${req.params.username} refCredits to $${refCredits}`,
      user: {
        username: user._id,
        refCredits: user.refCredits,
      }
    });
  } catch (error) {
    console.error('Failed to update user refCredits:', error);
    res.status(500).json({ error: 'Failed to update user refCredits' });
  }
});

router.patch('/users/:username/discord-id', requireAdmin, async (req: Request, res: Response) => {
  try {
    const { discordId } = req.body;

    // Validate discordId format: null to clear, or 17-19 digits
    if (discordId !== null && discordId !== '') {
      if (typeof discordId !== 'string' || !/^\d{17,19}$/.test(discordId)) {
        return res.status(400).json({ error: 'Discord ID must be 17-19 digits or null to clear' });
      }
    }

    const user = await userRepository.updateDiscordId(req.params.username, discordId || null);
    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    res.json({
      success: true,
      message: discordId ? `Updated Discord ID for ${req.params.username}` : `Cleared Discord ID for ${req.params.username}`,
      user: {
        username: user._id,
        discordId: user.discordId,
      }
    });
  } catch (error) {
    console.error('Failed to update user Discord ID:', error);
    res.status(500).json({ error: 'Failed to update user Discord ID' });
  }
});

// Add credits (increment) - admin only
router.post('/users/:username/credits/add', requireAdmin, async (req: Request, res: Response) => {
  try {
    const { amount, resetExpiration = true } = req.body;

    if (typeof amount !== 'number' || amount <= 0) {
      return res.status(400).json({ error: 'Amount must be a positive number' });
    }

    const user = await userRepository.addCredits(req.params.username, amount, resetExpiration);
    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }
    
    res.json({ 
      success: true, 
      message: `Added $${amount} credits to ${req.params.username}`,
      user: {
        username: user._id,
        credits: user.credits,
        expiresAt: user.expiresAt,
      }
    });
  } catch (error) {
    console.error('Failed to add user credits:', error);
    res.status(500).json({ error: 'Failed to add user credits' });
  }
});

// Add refCredits (increment) - admin only
router.post('/users/:username/refCredits/add', requireAdmin, async (req: Request, res: Response) => {
  try {
    const { amount } = req.body;

    if (typeof amount !== 'number' || amount <= 0) {
      return res.status(400).json({ error: 'Amount must be a positive number' });
    }

    const user = await userRepository.addRefCredits(req.params.username, amount);
    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    res.json({
      success: true,
      message: `Added $${amount} refCredits to ${req.params.username}`,
      user: {
        username: user._id,
        refCredits: user.refCredits,
      }
    });
  } catch (error) {
    console.error('Failed to add user refCredits:', error);
    res.status(500).json({ error: 'Failed to add user refCredits' });
  }
});

// CreditsNew (OpenHands) management - admin only
router.patch('/users/:username/creditsNew', requireAdmin, async (req: Request, res: Response) => {
  try {
    const { creditsNew, resetExpiration = true } = req.body;

    if (typeof creditsNew !== 'number' || creditsNew < 0) {
      return res.status(400).json({ error: 'CreditsNew must be a non-negative number' });
    }

    const user = await userRepository.setCreditsNew(req.params.username, creditsNew, resetExpiration);
    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    // Schedule expiration timer if credits > 0 and expiration was reset
    if (creditsNew > 0 && resetExpiration && user.expiresAtNew) {
      expirationSchedulerService.scheduleExpirationNew(req.params.username, user.expiresAtNew);
    }

    res.json({
      success: true,
      message: `Set creditsNew to $${creditsNew} for ${req.params.username}`,
      user: {
        username: user._id,
        creditsNew: user.creditsNew,
        expiresAtNew: user.expiresAtNew,
        purchasedAtNew: user.purchasedAtNew,
      }
    });
  } catch (error) {
    console.error('Failed to update user creditsNew:', error);
    res.status(500).json({ error: 'Failed to update user creditsNew' });
  }
});

router.post('/users/:username/creditsNew/add', requireAdmin, async (req: Request, res: Response) => {
  try {
    const { amount, resetExpiration = true } = req.body;

    if (typeof amount !== 'number' || amount <= 0) {
      return res.status(400).json({ error: 'Amount must be a positive number' });
    }

    const user = await userRepository.addCreditsNew(req.params.username, amount, resetExpiration);
    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    // Schedule expiration timer if expiration was reset
    if (resetExpiration && user.expiresAtNew) {
      expirationSchedulerService.scheduleExpirationNew(req.params.username, user.expiresAtNew);
    }

    res.json({
      success: true,
      message: `Added $${amount} creditsNew to ${req.params.username}`,
      user: {
        username: user._id,
        creditsNew: user.creditsNew,
        expiresAtNew: user.expiresAtNew,
        purchasedAtNew: user.purchasedAtNew,
      }
    });
  } catch (error) {
    console.error('Failed to add user creditsNew:', error);
    res.status(500).json({ error: 'Failed to add user creditsNew' });
  }
});

// Set credit package ($20 or $40) with 7-day expiry - admin only
router.post('/users/:username/credit-package', requireAdmin, async (req: Request, res: Response) => {
  try {
    const { package: pkg } = req.body;
    
    if (pkg !== '20' && pkg !== '40') {
      return res.status(400).json({ error: 'Package must be "20" or "40"' });
    }
    
    const credits = pkg === '40' ? 40 : 20;
    const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);
    
    const user = await userRepository.setCreditPackage(req.params.username, credits, expiresAt);
    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }
    
    res.json({ 
      success: true, 
      message: `Set $${credits} credit package for ${req.params.username}`,
      user: {
        username: user._id,
        credits: user.credits,
        expiresAt: user.expiresAt,
      }
    });
  } catch (error) {
    console.error('Failed to set credit package:', error);
    res.status(500).json({ error: 'Failed to set credit package' });
  }
});

// Generate referral codes for existing users without one
router.post('/generate-referral-codes', requireAdmin, async (req: Request, res: Response) => {
  try {
    const count = await userRepository.generateReferralCodeForExistingUsers();
    res.json({ 
      success: true, 
      message: `Generated referral codes for ${count} users`,
      updatedCount: count 
    });
  } catch (error) {
    console.error('Failed to generate referral codes:', error);
    res.status(500).json({ error: 'Failed to generate referral codes' });
  }
});

// Model Stats - admin only (for dashboard model usage breakdown)
router.get('/model-stats', requireAdmin, async (req: Request, res: Response) => {
  try {
    const period = (req.query.period as string) || 'all';
    let since: Date | undefined;
    
    const now = new Date();
    switch (period) {
      case '1h':
        since = new Date(now.getTime() - 60 * 60 * 1000);
        break;
      case '2h':
        since = new Date(now.getTime() - 2 * 60 * 60 * 1000);
        break;
      case '3h':
        since = new Date(now.getTime() - 3 * 60 * 60 * 1000);
        break;
      case '4h':
        since = new Date(now.getTime() - 4 * 60 * 60 * 1000);
        break;
      case '8h':
        since = new Date(now.getTime() - 8 * 60 * 60 * 1000);
        break;
      case '24h': {
        // Start of today in Vietnam timezone (UTC+7)
        // Midnight VN = 17:00 UTC previous day
        const vnOffsetMs = 7 * 60 * 60 * 1000;
        const nowInVN = now.getTime() + vnOffsetMs;
        const startOfTodayVN = new Date(nowInVN);
        startOfTodayVN.setUTCHours(0, 0, 0, 0);
        since = new Date(startOfTodayVN.getTime() - vnOffsetMs);
        break;
      }
      case '3d':
        since = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000);
        break;
      case '7d':
        since = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case '30d':
        since = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        break;
      default:
        since = undefined;
    }
    
    const stats = await requestLogRepository.getModelStats(since);
    res.json({ models: stats, period });
  } catch (error) {
    console.error('Failed to get model stats:', error);
    res.status(500).json({ error: 'Failed to get model stats' });
  }
});

// Payments - admin only (for billing dashboard)
router.get('/payments', requireAdmin, async (req: Request, res: Response) => {
  try {
    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 20;
    const status = req.query.status as PaymentStatus | undefined;
    const period = (req.query.period as string) || 'all';
    
    let since: Date | undefined;
    let until: Date | undefined;
    const now = new Date();

    // Check for custom date range
    const fromDate = req.query.from as string;
    const toDate = req.query.to as string;

    if (fromDate) {
      since = new Date(fromDate);
      since.setHours(0, 0, 0, 0);
    }
    if (toDate) {
      until = new Date(toDate);
      until.setHours(23, 59, 59, 999);
    }

    // If no custom date, use period presets
    if (!fromDate && !toDate) {
      switch (period) {
        case '1h':
          since = new Date(now.getTime() - 60 * 60 * 1000);
          break;
        case '2h':
          since = new Date(now.getTime() - 2 * 60 * 60 * 1000);
          break;
        case '3h':
          since = new Date(now.getTime() - 3 * 60 * 60 * 1000);
          break;
        case '24h': {
          // Start of today in Vietnam timezone (UTC+7)
          // Midnight VN = 17:00 UTC previous day
          const vnOffsetMs = 7 * 60 * 60 * 1000;
          const nowInVN = now.getTime() + vnOffsetMs;
          const startOfTodayVN = new Date(nowInVN);
          startOfTodayVN.setUTCHours(0, 0, 0, 0);
          since = new Date(startOfTodayVN.getTime() - vnOffsetMs);
          break;
        }
        case '7d':
          since = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
          break;
        case '30d':
          since = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
          break;
        default:
          since = undefined;
      }
    }
    
    const [result, stats] = await Promise.all([
      paymentRepository.getAllPayments({ page, limit, status, since, until }),
      paymentRepository.getPaymentStats(since, until),
    ]);
    
    res.json({
      payments: result.payments.map(p => ({
        id: p._id,
        userId: p.userId,
        username: p.username,
        credits: p.credits,
        amount: p.amount,
        currency: p.currency,
        status: p.status,
        orderCode: p.orderCode,
        createdAt: p.createdAt,
        completedAt: p.completedAt,
        profitVND: p.profitVND || 0,
      })),
      pagination: {
        page: result.page,
        totalPages: result.totalPages,
        total: result.total,
        limit,
      },
      stats: {
        ...stats,
        totalProfit: stats.totalProfit || 0,
      },
      period,
    });
  } catch (error) {
    console.error('Failed to get payments:', error);
    res.status(500).json({ error: 'Failed to get payments' });
  }
});

export default router;
