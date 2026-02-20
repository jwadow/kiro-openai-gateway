import { Router, Request, Response } from 'express';
import { userService } from '../services/user.service.js';
import { migrationService, MigrationError } from '../services/migration.service.js';
import { jwtAuth } from '../middleware/auth.middleware.js';
import { requestLogRepository } from '../repositories/request-log.repository.js';
import { userRepository } from '../repositories/user.repository.js';
import { maskUsername } from '../models/user-new.model.js';

const router = Router();

router.get('/me', jwtAuth, async (req: Request, res: Response) => {
  try {
    const username = (req as any).user?.username;
    if (!username) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const profile = await userService.getProfile(username);
    if (!profile) {
      return res.status(404).json({ error: 'User not found' });
    }

    res.json(profile);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.get('/api-key', jwtAuth, async (req: Request, res: Response) => {
  try {
    const username = (req as any).user?.username;
    if (!username) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const apiKey = await userService.getFullApiKey(username);
    if (!apiKey) {
      return res.status(404).json({ error: 'API key not found' });
    }

    res.json({ apiKey });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.post('/api-key/rotate', jwtAuth, async (req: Request, res: Response) => {
  try {
    const username = (req as any).user?.username;
    if (!username) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const result = await userService.rotateApiKey(username);
    res.json({
      newApiKey: result.newApiKey,
      oldKeyInvalidated: true,
      createdAt: result.createdAt,
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.get('/billing', jwtAuth, async (req: Request, res: Response) => {
  try {
    const username = (req as any).user?.username;
    if (!username) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const billing = await userService.getBillingInfo(username);
    if (!billing) {
      return res.status(404).json({ error: 'Billing info not found' });
    }

    res.json(billing);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// TEMPORARILY DISABLED - request history
// router.get('/request-history', jwtAuth, async (req: Request, res: Response) => {
//   try {
//     const username = (req as any).user?.username;
//     if (!username) {
//       return res.status(401).json({ error: 'Unauthorized' });
//     }
//
//     const page = parseInt(req.query.page as string) || 1;
//     const limit = parseInt(req.query.limit as string) || 20;
//     const from = req.query.from ? new Date(req.query.from as string) : undefined;
//     const to = req.query.to ? new Date(req.query.to as string) : undefined;
//
//     const result = await requestLogRepository.findByUserId({
//       userId: username,
//       page,
//       limit,
//       from,
//       to,
//     });
//
//     res.json(result);
//   } catch (error: any) {
//     res.status(500).json({ error: error.message });
//   }
// });
router.get('/request-history', jwtAuth, (req: Request, res: Response) => {
  res.status(503).json({ error: 'Request history is temporarily disabled' });
});

router.get('/credits-usage', jwtAuth, async (req: Request, res: Response) => {
  try {
    const username = (req as any).user?.username;
    if (!username) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const usage = await requestLogRepository.getCreditsUsageByPeriod(username);
    res.json({
      last1h: usage.last1h,
      last24h: usage.last24h,
      last7d: usage.last7d,
      last30d: usage.last30d,
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.get('/detailed-usage', jwtAuth, async (req: Request, res: Response) => {
  try {
    const username = (req as any).user?.username;
    if (!username) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const period = (req.query.period as '1h' | '24h' | '7d' | '30d') || '24h';
    const validPeriods = ['1h', '24h', '7d', '30d'];
    if (!validPeriods.includes(period)) {
      return res.status(400).json({ error: 'Invalid period. Use: 1h, 24h, 7d, or 30d' });
    }

    const usage = await requestLogRepository.getDetailedUsageByPeriod(username, period);
    res.json(usage);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.get('/request-logs', jwtAuth, async (req: Request, res: Response) => {
  try {
    const username = (req as any).user?.username;
    if (!username) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const period = (req.query.period as '1h' | '24h' | '7d' | '30d') || '24h';
    const validPeriods = ['1h', '24h', '7d', '30d'];
    if (!validPeriods.includes(period)) {
      return res.status(400).json({ error: 'Invalid period. Use: 1h, 24h, 7d, or 30d' });
    }

    const page = parseInt(req.query.page as string) || 1;
    const limit = Math.min(parseInt(req.query.limit as string) || 50, 100);

    const logs = await requestLogRepository.getRequestLogsByPeriod(username, period, page, limit);
    res.json(logs);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.patch('/discord-id', jwtAuth, async (req: Request, res: Response) => {
  try {
    const username = (req as any).user?.username;
    if (!username) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const { discordId } = req.body as { discordId?: string };

    // Allow empty string or null to clear Discord ID
    const normalizedDiscordId = discordId?.trim() || null;

    const result = await userService.updateDiscordId(username, normalizedDiscordId);
    res.json(result);
  } catch (error: any) {
    if (error.message === 'Invalid Discord ID format') {
      return res.status(400).json({ error: error.message });
    }
    res.status(500).json({ error: error.message });
  }
});

// Referral system disabled
// router.get('/referral', jwtAuth, async (req: Request, res: Response) => {
//   try {
//     const username = (req as any).user?.username;
//     if (!username) {
//       return res.status(401).json({ error: 'Unauthorized' });
//     }

//     const user = await userRepository.getFullUser(username);
//     if (!user) {
//       return res.status(404).json({ error: 'User not found' });
//     }

//     const baseUrl = process.env.FRONTEND_URL || 'https://trollllm.xyz';
//     const referralLink = `${baseUrl}/register?ref=${user.referralCode}`;

//     res.json({
//       referralCode: user.referralCode,
//       referralLink,
//       refCredits: user.refCredits || 0,
//     });
//   } catch (error: any) {
//     res.status(500).json({ error: error.message });
//   }
// });

// router.get('/referral/stats', jwtAuth, async (req: Request, res: Response) => {
//   try {
//     const username = (req as any).user?.username;
//     if (!username) {
//       return res.status(401).json({ error: 'Unauthorized' });
//     }

//     const stats = await userRepository.getReferralStats(username);
//     res.json(stats);
//   } catch (error: any) {
//     res.status(500).json({ error: error.message });
//   }
// });

// router.get('/referral/list', jwtAuth, async (req: Request, res: Response) => {
//   try {
//     const username = (req as any).user?.username;
//     if (!username) {
//       return res.status(401).json({ error: 'Unauthorized' });
//     }

//     const referredUsers = await userRepository.getReferredUsers(username);

//     // Mask usernames for privacy
//     const maskedUsers = referredUsers.map(u => ({
//       ...u,
//       username: maskUsername(u.username),
//     }));

//     res.json({ users: maskedUsers });
//   } catch (error: any) {
//     res.status(500).json({ error: error.message });
//   }
// });

// Migration endpoint
router.post('/migrate', jwtAuth, async (req: Request, res: Response) => {
  try {
    const username = (req as any).user?.username;
    if (!username) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const result = await migrationService.processMigration(username);
    res.json(result);
  } catch (error: any) {
    if (error instanceof MigrationError) {
      if (error.message === 'User has already migrated') {
        return res.status(400).json({ error: error.message });
      }
      return res.status(400).json({ error: error.message });
    }
    res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;
