import { Router, Request, Response } from 'express';
import { z } from 'zod';
import mongoose from 'mongoose';
import * as openhandsService from '../services/openhands.service.js';

const router = Router();

// Validation schemas
const createKeySchema = z.object({
  id: z.string().min(1).max(50),
  apiKey: z.string().min(1),
});

const createBindingSchema = z.object({
  proxyId: z.string().min(1),
  openhandsKeyId: z.string().min(1),
  priority: z.number().int().min(1).max(10),
});

const updateBindingSchema = z.object({
  priority: z.number().int().min(1).max(10).optional(),
  isActive: z.boolean().optional(),
});

// ============ KEYS ============

// GET /admin/openhands/keys - List all keys
router.get('/keys', async (_req: Request, res: Response) => {
  try {
    const keys = await openhandsService.listKeys();
    const stats = await openhandsService.getStats();
    
    // Mask API keys for security
    const maskedKeys = keys.map(k => ({
      ...k,
      apiKey: k.apiKey ? `${k.apiKey.slice(0, 8)}...${k.apiKey.slice(-4)}` : '***',
    }));
    
    res.json({ keys: maskedKeys, ...stats });
  } catch (error) {
    console.error('Error listing OpenHands keys:', error);
    res.status(500).json({ error: 'Failed to list keys' });
  }
});

// POST /admin/openhands/keys - Create key
router.post('/keys', async (req: Request, res: Response) => {
  try {
    const input = createKeySchema.parse(req.body);
    const key = await openhandsService.createKey(input);
    
    res.status(201).json({
      ...key,
      apiKey: `${key.apiKey.slice(0, 8)}...${key.apiKey.slice(-4)}`,
    });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return res.status(400).json({ error: 'Invalid input', details: error.errors });
    }
    console.error('Error creating OpenHands key:', error);
    res.status(500).json({ error: 'Failed to create key' });
  }
});

// DELETE /admin/openhands/keys/:id - Delete key
router.delete('/keys/:id', async (req: Request, res: Response) => {
  try {
    const deleted = await openhandsService.deleteKey(req.params.id);
    if (!deleted) {
      return res.status(404).json({ error: 'Key not found' });
    }
    res.json({ success: true, message: 'Key and its bindings deleted' });
  } catch (error) {
    console.error('Error deleting OpenHands key:', error);
    res.status(500).json({ error: 'Failed to delete key' });
  }
});

// POST /admin/openhands/keys/:id/reset - Reset key stats
router.post('/keys/:id/reset', async (req: Request, res: Response) => {
  try {
    const key = await openhandsService.resetKeyStats(req.params.id);
    if (!key) {
      return res.status(404).json({ error: 'Key not found' });
    }
    res.json({ success: true, message: 'Key stats reset' });
  } catch (error) {
    console.error('Error resetting OpenHands key:', error);
    res.status(500).json({ error: 'Failed to reset key' });
  }
});

// ============ BINDINGS ============

// GET /admin/openhands/bindings - List all bindings
router.get('/bindings', async (_req: Request, res: Response) => {
  try {
    const [bindings, proxies, keys] = await Promise.all([
      openhandsService.listBindings(),
      openhandsService.listProxies(),
      openhandsService.listKeys(),
    ]);

    // Create lookup maps
    const proxyMap = new Map(proxies.map(p => [p._id, p]));
    const keyMap = new Map(keys.map(k => [k._id, k]));

    // Check for orphaned bindings (key doesn't exist)
    const hasOrphanedBindings = bindings.some(b => !keyMap.has(b.openhandsKeyId));

    // Auto-repair if orphaned bindings found
    if (hasOrphanedBindings) {
      console.log('[OpenHands] Detected orphaned bindings, auto-repairing...');
      const repairResult = await openhandsService.repairBindings();
      if (repairResult.repaired > 0 || repairResult.deleted > 0) {
        console.log(`[OpenHands] Auto-repair: ${repairResult.repaired} fixed, ${repairResult.deleted} removed`);
        // Re-fetch bindings after repair
        const updatedBindings = await openhandsService.listBindings();
        const updatedKeys = await openhandsService.listKeys();
        const updatedKeyMap = new Map(updatedKeys.map(k => [k._id, k]));

        // Enrich with updated data
        const enrichedBindings = updatedBindings.map(b => ({
          ...b,
          proxyName: proxyMap.get(b.proxyId)?.name || b.proxyId,
          keyStatus: updatedKeyMap.get(b.openhandsKeyId)?.status || 'unknown',
          keyTotalSpend: updatedKeyMap.get(b.openhandsKeyId)?.totalSpend || 0,
        }));

        // Group by proxy
        const byProxy: Record<string, typeof enrichedBindings> = {};
        for (const binding of enrichedBindings) {
          if (!byProxy[binding.proxyId]) {
            byProxy[binding.proxyId] = [];
          }
          byProxy[binding.proxyId].push(binding);
        }

        return res.json({
          total: updatedBindings.length,
          bindings: enrichedBindings,
          byProxy,
          proxies: proxies.map(p => ({ _id: p._id, name: p.name, status: p.status, isActive: p.isActive })),
          keys: updatedKeys.map(k => ({ _id: k._id, status: k.status })),
          autoRepaired: { repaired: repairResult.repaired, deleted: repairResult.deleted },
        });
      }
    }

    // Enrich bindings with names (normal case)
    const enrichedBindings = bindings.map(b => ({
      ...b,
      proxyName: proxyMap.get(b.proxyId)?.name || b.proxyId,
      keyStatus: keyMap.get(b.openhandsKeyId)?.status || 'unknown',
      keyTotalSpend: keyMap.get(b.openhandsKeyId)?.totalSpend || 0,
    }));

    // Group by proxy
    const byProxy: Record<string, typeof enrichedBindings> = {};
    for (const binding of enrichedBindings) {
      if (!byProxy[binding.proxyId]) {
        byProxy[binding.proxyId] = [];
      }
      byProxy[binding.proxyId].push(binding);
    }

    res.json({
      total: bindings.length,
      bindings: enrichedBindings,
      byProxy,
      proxies: proxies.map(p => ({ _id: p._id, name: p.name, status: p.status, isActive: p.isActive })),
      keys: keys.map(k => ({ _id: k._id, status: k.status })),
    });
  } catch (error) {
    console.error('Error listing bindings:', error);
    res.status(500).json({ error: 'Failed to list bindings' });
  }
});

// GET /admin/openhands/bindings/:proxyId - Get bindings for a proxy
router.get('/bindings/:proxyId', async (req: Request, res: Response) => {
  try {
    const bindings = await openhandsService.getBindingsForProxy(req.params.proxyId);
    res.json({ bindings });
  } catch (error) {
    console.error('Error getting bindings:', error);
    res.status(500).json({ error: 'Failed to get bindings' });
  }
});

// POST /admin/openhands/bindings - Create binding
router.post('/bindings', async (req: Request, res: Response) => {
  try {
    const input = createBindingSchema.parse(req.body);
    const binding = await openhandsService.createBinding(input);
    res.status(201).json(binding);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return res.status(400).json({ error: 'Invalid input', details: error.errors });
    }
    console.error('Error creating binding:', error);
    res.status(500).json({ error: 'Failed to create binding' });
  }
});

// PATCH /admin/openhands/bindings/:proxyId/:keyId - Update binding
router.patch('/bindings/:proxyId/:keyId', async (req: Request, res: Response) => {
  try {
    const input = updateBindingSchema.parse(req.body);
    const binding = await openhandsService.updateBinding(req.params.proxyId, req.params.keyId, input);
    if (!binding) {
      return res.status(404).json({ error: 'Binding not found' });
    }
    res.json(binding);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return res.status(400).json({ error: 'Invalid input', details: error.errors });
    }
    console.error('Error updating binding:', error);
    res.status(500).json({ error: 'Failed to update binding' });
  }
});

// DELETE /admin/openhands/bindings/:proxyId/:keyId - Delete binding
router.delete('/bindings/:proxyId/:keyId', async (req: Request, res: Response) => {
  try {
    const deleted = await openhandsService.deleteBinding(req.params.proxyId, req.params.keyId);
    if (!deleted) {
      return res.status(404).json({ error: 'Binding not found' });
    }
    res.json({ success: true, message: 'Binding deleted' });
  } catch (error) {
    console.error('Error deleting binding:', error);
    res.status(500).json({ error: 'Failed to delete binding' });
  }
});

// DELETE /admin/openhands/bindings/:proxyId - Delete all bindings for a proxy
router.delete('/bindings/:proxyId', async (req: Request, res: Response) => {
  try {
    const count = await openhandsService.deleteAllBindingsForProxy(req.params.proxyId);
    res.json({ success: true, message: `Deleted ${count} bindings` });
  } catch (error) {
    console.error('Error deleting bindings:', error);
    res.status(500).json({ error: 'Failed to delete bindings' });
  }
});

// ============ STATS ============

// GET /admin/openhands/stats - Get stats
router.get('/stats', async (_req: Request, res: Response) => {
  try {
    const stats = await openhandsService.getStats();
    res.json(stats);
  } catch (error) {
    console.error('Error getting stats:', error);
    res.status(500).json({ error: 'Failed to get stats' });
  }
});

// ============ SPEND MONITORING ============

// GET /admin/openhands/spend-summary - Get spend summary for all keys
router.get('/spend-summary', async (_req: Request, res: Response) => {
  try {
    const keys = await openhandsService.listKeys();
    
    const summary = {
      total_keys: keys.length,
      healthy_keys: keys.filter(k => k.status === 'healthy').length,
      threshold: 9.8,
      keys: keys.map(k => ({
        id: k._id,
        status: k.status,
        total_spend: k.totalSpend || 0,
        last_spend_check: k.lastSpendCheck,
        last_used_at: k.lastUsedAt,
        spend_percentage: ((k.totalSpend || 0) / 9.8) * 100,
      })),
    };

    res.json(summary);
  } catch (error) {
    console.error('Error getting spend summary:', error);
    res.status(500).json({ error: 'Failed to get spend summary' });
  }
});

// GET /admin/openhands/spend-history - Get spend check history
router.get('/spend-history', async (req: Request, res: Response) => {
  try {
    const limit = parseInt(req.query.limit as string) || 100;
    const keyId = req.query.keyId as string;
    
    const filter: Record<string, unknown> = {};
    if (keyId) filter.keyId = keyId;

    const history = await mongoose.connection.db!
      .collection('openhands_key_spend_history')
      .find(filter)
      .sort({ checkedAt: -1 })
      .limit(limit)
      .toArray();

    res.json({
      total: history.length,
      history: history.map(h => ({
        key_id: h.keyId,
        api_key_masked: h.apiKeyMasked,
        spend: h.spend,
        threshold: h.threshold,
        checked_at: h.checkedAt,
        was_active: h.wasActive,
        rotated_at: h.rotatedAt,
        rotation_reason: h.rotationReason,
        new_key_id: h.newKeyId,
      })),
    });
  } catch (error) {
    console.error('Error getting spend history:', error);
    res.status(500).json({ error: 'Failed to get spend history' });
  }
});

// ============ BACKUP KEYS ============

// GET /admin/openhands/backup-keys - List backup keys
router.get('/backup-keys', async (_req: Request, res: Response) => {
  try {
    const [keys, stats] = await Promise.all([
      openhandsService.listBackupKeys(),
      openhandsService.getBackupKeyStats(),
    ]);

    // Mask API keys and add deletesAt for used keys
    const maskedKeys = keys.map(k => {
      const keyData: any = {
        id: k._id,
        maskedApiKey: k.apiKey ? `${k.apiKey.slice(0, 8)}...${k.apiKey.slice(-4)}` : '***',
        isUsed: k.isUsed,
        activated: k.activated,
        usedFor: k.usedFor,
        usedAt: k.usedAt,
        createdAt: k.createdAt,
      };

      // Add deletesAt for used keys (usedAt + 6 hours)
      if (k.isUsed && k.usedAt) {
        const deletesAt = new Date(k.usedAt);
        deletesAt.setHours(deletesAt.getHours() + 6);
        keyData.deletesAt = deletesAt;
      }

      return keyData;
    });

    res.json({ keys: maskedKeys, ...stats });
  } catch (error) {
    console.error('Error listing backup keys:', error);
    res.status(500).json({ error: 'Failed to list backup keys' });
  }
});

// POST /admin/openhands/backup-keys - Create backup key
router.post('/backup-keys', async (req: Request, res: Response) => {
  try {
    const input = createKeySchema.parse(req.body);
    const key = await openhandsService.createBackupKey(input);
    
    res.status(201).json({
      id: key._id,
      maskedApiKey: `${key.apiKey.slice(0, 8)}...${key.apiKey.slice(-4)}`,
      isUsed: key.isUsed,
      activated: key.activated,
      createdAt: key.createdAt,
    });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return res.status(400).json({ error: 'Invalid input', details: error.errors });
    }
    console.error('Error creating backup key:', error);
    res.status(500).json({ error: 'Failed to create backup key' });
  }
});

// DELETE /admin/openhands/backup-keys/:id - Delete backup key
router.delete('/backup-keys/:id', async (req: Request, res: Response) => {
  try {
    const deleted = await openhandsService.deleteBackupKey(req.params.id);
    if (!deleted) {
      return res.status(404).json({ error: 'Backup key not found' });
    }
    res.json({ success: true, message: 'Backup key deleted' });
  } catch (error) {
    console.error('Error deleting backup key:', error);
    res.status(500).json({ error: 'Failed to delete backup key' });
  }
});

// POST /admin/openhands/backup-keys/:id/restore - Restore backup key
router.post('/backup-keys/:id/restore', async (req: Request, res: Response) => {
  try {
    const restored = await openhandsService.restoreBackupKey(req.params.id);
    if (!restored) {
      return res.status(404).json({ error: 'Backup key not found' });
    }
    res.json({ success: true, message: 'Backup key restored' });
  } catch (error) {
    console.error('Error restoring backup key:', error);
    res.status(500).json({ error: 'Failed to restore backup key' });
  }
});

// ============ RELOAD ============

// POST /admin/openhands/reload - Reload all pools on goproxy
router.post('/reload', async (_req: Request, res: Response) => {
  try {
    // Try GOPROXY_URL first, then OPENHANDS_PROXY_PORT, then default ports
    const goproxyUrl = process.env.GOPROXY_URL;
    const openhandsPort = process.env.OPENHANDS_PROXY_PORT || '8004';
    const defaultPort = process.env.PROXY_PORT || '8003';

    // URLs to try in order
    const urlsToTry = goproxyUrl
      ? [`${goproxyUrl}/reload`]
      : [
          `http://localhost:${openhandsPort}/reload`,  // OpenHands port first
          `http://localhost:${defaultPort}/reload`,    // Default port fallback
        ];

    let lastError: string | null = null;

    for (const url of urlsToTry) {
      try {
        console.log(`[OpenHands] Trying reload at: ${url}`);
        const response = await fetch(url, {
          method: 'POST',
          signal: AbortSignal.timeout(5000) // 5 second timeout
        });

        if (response.ok) {
          const data = await response.json();
          console.log(`[OpenHands] Reload successful at ${url}`);
          return res.json(data);
        }

        lastError = await response.text();
        console.error(`[OpenHands] Reload failed at ${url}:`, lastError);
      } catch (error: any) {
        lastError = error.message;
        console.error(`[OpenHands] Connection failed to ${url}:`, error.message);
      }
    }

    res.status(500).json({ error: 'Failed to connect to goproxy', details: lastError });
  } catch (error: any) {
    console.error('Error reloading goproxy:', error);
    res.status(500).json({ error: 'Failed to connect to goproxy', details: error.message });
  }
});

// ============ REPAIR ============

// POST /admin/openhands/repair-bindings - Auto-repair orphaned bindings
router.post('/repair-bindings', async (_req: Request, res: Response) => {
  try {
    const result = await openhandsService.repairBindings();

    if (result.repaired > 0 || result.deleted > 0) {
      console.log(`[OpenHands] Repaired ${result.repaired} bindings, deleted ${result.deleted} orphaned bindings`);
    }

    res.json({
      success: true,
      message: `Checked ${result.checked} bindings: ${result.repaired} repaired, ${result.deleted} deleted`,
      ...result,
    });
  } catch (error) {
    console.error('Error repairing bindings:', error);
    res.status(500).json({ error: 'Failed to repair bindings' });
  }
});

export default router;
