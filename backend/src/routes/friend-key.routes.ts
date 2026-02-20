import { Router, Request, Response } from 'express';
import { friendKeyService } from '../services/friend-key.service.js';
import { jwtAuth } from '../middleware/auth.middleware.js';
import { checkMigration } from '../middleware/migration-check.js';
import { UpdateModelLimitsDto } from '../dtos/friend-key.dto.js';
import { requestLogRepository } from '../repositories/request-log.repository.js';

const router = Router();

// Get friend key info
router.get('/', jwtAuth, checkMigration, async (req: Request, res: Response) => {
  try {
    const username = (req as any).user?.username;
    if (!username) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const friendKey = await friendKeyService.getFriendKey(username);
    if (!friendKey) {
      return res.status(404).json({ error: 'No Friend Key found', hasKey: false });
    }

    res.json({ ...friendKey, hasKey: true });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Get full friend key (reveal)
router.get('/reveal', jwtAuth, checkMigration, async (req: Request, res: Response) => {
  try {
    const username = (req as any).user?.username;
    if (!username) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const friendKey = await friendKeyService.getFullFriendKey(username);
    if (!friendKey) {
      return res.status(404).json({ error: 'No Friend Key found' });
    }

    res.json({ friendKey });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Create friend key
router.post('/', jwtAuth, checkMigration, async (req: Request, res: Response) => {
  try {
    const username = (req as any).user?.username;
    if (!username) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const result = await friendKeyService.createFriendKey(username);
    res.status(201).json(result);
  } catch (error: any) {
    if (error.message.includes('already exists')) {
      return res.status(409).json({ error: error.message });
    }
    res.status(500).json({ error: error.message });
  }
});

// Rotate friend key
router.post('/rotate', jwtAuth, checkMigration, async (req: Request, res: Response) => {
  try {
    const username = (req as any).user?.username;
    if (!username) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const result = await friendKeyService.rotateFriendKey(username);
    res.json(result);
  } catch (error: any) {
    if (error.message.includes('No Friend Key found')) {
      return res.status(404).json({ error: error.message });
    }
    res.status(500).json({ error: error.message });
  }
});

// Delete friend key
router.delete('/', jwtAuth, checkMigration, async (req: Request, res: Response) => {
  try {
    const username = (req as any).user?.username;
    if (!username) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const deleted = await friendKeyService.deleteFriendKey(username);
    if (!deleted) {
      return res.status(404).json({ error: 'No Friend Key found' });
    }

    res.json({ success: true, message: 'Friend Key deleted' });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Update model limits
router.put('/limits', jwtAuth, checkMigration, async (req: Request, res: Response) => {
  try {
    const username = (req as any).user?.username;
    if (!username) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const parseResult = UpdateModelLimitsDto.safeParse(req.body);
    if (!parseResult.success) {
      return res.status(400).json({ 
        error: 'Invalid request body', 
        details: parseResult.error.errors 
      });
    }

    const result = await friendKeyService.updateModelLimits(username, parseResult.data.modelLimits);
    if (!result) {
      return res.status(404).json({ error: 'No Friend Key found. Create one first.' });
    }

    res.json(result);
  } catch (error: any) {
    if (error.message.includes('Invalid model')) {
      return res.status(400).json({ error: error.message });
    }
    res.status(500).json({ error: error.message });
  }
});

// Get model usage breakdown
router.get('/usage', jwtAuth, async (req: Request, res: Response) => {
  try {
    const username = (req as any).user?.username;
    if (!username) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const usage = await friendKeyService.getModelUsage(username);
    res.json({ models: usage });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Get friend key activity log
router.get('/activity', jwtAuth, async (req: Request, res: Response) => {
  try {
    const username = (req as any).user?.username;
    if (!username) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const page = parseInt(req.query.page as string) || 1;
    const limit = Math.min(parseInt(req.query.limit as string) || 20, 100);

    const result = await requestLogRepository.findByUserId({
      userId: username,
      page,
      limit,
      friendKeyOnly: true,
    });

    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

export default router;
