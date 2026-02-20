import { Router, Request, Response } from 'express';
import { z } from 'zod';
import * as openhandsService from '../services/openhands.service.js';
import { webhookAuthMiddleware } from '../middleware/webhook-auth.middleware.js';

const router = Router();

// Apply webhook authentication to all routes
router.use(webhookAuthMiddleware);

// Validation schema for adding a new key
const addKeySchema = z.object({
  apiKey: z.string().min(1, 'API key is required'),
  replaceKeyId: z.string().optional(),  // ID of the old key to replace/delete
  name: z.string().optional(),  // Name from third-party (e.g., "tai-p1" from Python script)
});

/**
 * GET /webhook/openhands/status
 * Check if any OpenHands API keys have 'need_refresh' status.
 * Used by third-party scripts to know when keys need rotation.
 */
router.get('/openhands/status', async (_req: Request, res: Response) => {
  try {
    const keys = await openhandsService.listKeys();
    
    // Filter keys with need_refresh status
    const needRefreshKeys = keys.filter(k => k.status === 'need_refresh');
    
    res.json({
      need_refresh: needRefreshKeys.length > 0,
      count: needRefreshKeys.length,
      keys: needRefreshKeys.map(k => ({
        id: k._id,
        apiKey: k.apiKey,  // Full unmasked key as per user request
        status: k.status,
        lastError: k.lastError,
        lastUsedAt: k.lastUsedAt,
        createdAt: k.createdAt,
      })),
    });
  } catch (error) {
    console.error('[Webhook] Error getting key status:', error);
    res.status(500).json({ error: 'Failed to get key status' });
  }
});

/**
 * POST /webhook/openhands/keys
 * Add a new OpenHands API key and bind it to proxy-6.
 * If replaceKeyId is provided, delete ONLY that specific key first.
 * Key name can be provided by third-party (e.g., "tai-p1" from Python script).
 * If no name provided, defaults to "oh-key" prefix.
 */
router.post('/openhands/keys', async (req: Request, res: Response) => {
  try {
    // Validate request body
    const input = addKeySchema.parse(req.body);
    
    let deletedKey: string | null = null;
    
    // Step 1: If replaceKeyId provided, delete ONLY that specific key
    if (input.replaceKeyId) {
      try {
        const deleted = await openhandsService.deleteKey(input.replaceKeyId);
        if (deleted) {
          deletedKey = input.replaceKeyId;
          console.log(`[Webhook] Deleted old key: ${input.replaceKeyId}`);
        } else {
          console.log(`[Webhook] Key not found for deletion: ${input.replaceKeyId}`);
        }
      } catch (deleteError: any) {
        console.error(`[Webhook] Failed to delete key ${input.replaceKeyId}:`, deleteError);
      }
    }
    
    // Step 2: Generate unique key ID and create new key
    // Use provided name or fallback to "oh-key" prefix
    const keyPrefix = input.name || 'oh-key';
    const keyId = `${keyPrefix}-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;
    
    const key = await openhandsService.createKey({
      id: keyId,
      apiKey: input.apiKey,
    });
    
    console.log(`[Webhook] Created new key: ${keyId}`);
    
    // Step 3: Bind new key to proxy-6 with priority 1
    let binding = null;
    let bindingWarning: string | undefined;
    
    try {
      binding = await openhandsService.createBinding({
        proxyId: 'proxy-6',
        openhandsKeyId: keyId,
        priority: 1,
      });
      console.log(`[Webhook] Bound key ${keyId} to proxy-6`);
    } catch (bindError: any) {
      console.error('[Webhook] Failed to create binding for key:', keyId, bindError);
      bindingWarning = `Key created but binding to proxy-6 failed: ${bindError.message}`;
    }
    
    res.status(201).json({
      success: true,
      key: {
        id: key._id,
        apiKey: key.apiKey,  // Full unmasked key
        status: key.status,
        createdAt: key.createdAt,
      },
      binding: binding ? {
        proxyId: binding.proxyId,
        priority: binding.priority,
        isActive: binding.isActive,
      } : null,
      replaced_key: deletedKey,
      binding_warning: bindingWarning,
    });
  } catch (error) {
    if (error instanceof z.ZodError) {
      res.status(400).json({ error: 'Invalid input', details: error.errors });
      return;
    }
    console.error('[Webhook] Error adding key:', error);
    res.status(500).json({ error: 'Failed to add key' });
  }
});

export default router;
