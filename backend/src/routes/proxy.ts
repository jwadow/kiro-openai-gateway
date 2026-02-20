import { Router, Request, Response } from 'express';
import { z } from 'zod';
import * as proxyService from '../services/proxy.service.js';

const router = Router();

// Validation schemas
const createProxySchema = z.object({
  name: z.string().min(1).max(100),
  type: z.enum(['http', 'socks5']),
  host: z.string().min(1),
  port: z.number().int().min(1).max(65535),
  username: z.string().optional(),
  password: z.string().optional(),
});

const updateProxySchema = z.object({
  name: z.string().min(1).max(100).optional(),
  host: z.string().min(1).optional(),
  port: z.number().int().min(1).max(65535).optional(),
  username: z.string().optional(),
  password: z.string().optional(),
  isActive: z.boolean().optional(),
});

const bindKeySchema = z.object({
  factoryKeyId: z.string().min(1),
  priority: z.number().int().min(1).max(10),
});

const updateBindingSchema = z.object({
  priority: z.number().int().min(1).max(10).optional(),
  isActive: z.boolean().optional(),
});

// GET /admin/proxies - List all proxies
router.get('/', async (_req: Request, res: Response) => {
  try {
    const proxies = await proxyService.listProxies();
    const stats = await proxyService.getProxyStats();

    res.json({
      ...stats,
      proxies,
    });
  } catch (error) {
    console.error('Error listing proxies:', error);
    res.status(500).json({ error: 'Failed to list proxies' });
  }
});

// GET /admin/proxies/bindings - Get all bindings overview
router.get('/bindings', async (_req: Request, res: Response) => {
  try {
    const bindings = await proxyService.getAllBindings();
    
    // Group bindings by proxy
    const byProxy: Record<string, typeof bindings> = {};
    for (const binding of bindings) {
      if (!byProxy[binding.proxyId]) {
        byProxy[binding.proxyId] = [];
      }
      byProxy[binding.proxyId].push(binding);
    }

    res.json({
      total: bindings.length,
      bindings,
      byProxy,
    });
  } catch (error) {
    console.error('Error listing all bindings:', error);
    res.status(500).json({ error: 'Failed to list bindings' });
  }
});

// POST /admin/proxies - Create proxy
router.post('/', async (req: Request, res: Response) => {
  try {
    const input = createProxySchema.parse(req.body);
    const proxy = await proxyService.createProxy(input);

    res.status(201).json(proxy);
  } catch (error) {
    if (error instanceof z.ZodError) {
      res.status(400).json({ error: 'Invalid input', details: error.errors });
      return;
    }
    console.error('Error creating proxy:', error);
    res.status(500).json({ error: 'Failed to create proxy' });
  }
});

// GET /admin/proxies/:id - Get proxy details
router.get('/:id', async (req: Request, res: Response) => {
  try {
    const proxy = await proxyService.getProxy(req.params.id);
    if (!proxy) {
      res.status(404).json({ error: 'Proxy not found' });
      return;
    }

    const bindings = await proxyService.getProxyBindings(req.params.id);
    res.json({ ...proxy, bindings });
  } catch (error) {
    console.error('Error getting proxy:', error);
    res.status(500).json({ error: 'Failed to get proxy' });
  }
});

// PATCH /admin/proxies/:id - Update proxy
router.patch('/:id', async (req: Request, res: Response) => {
  try {
    const input = updateProxySchema.parse(req.body);
    const proxy = await proxyService.updateProxy(req.params.id, input);

    if (!proxy) {
      res.status(404).json({ error: 'Proxy not found' });
      return;
    }

    res.json(proxy);
  } catch (error) {
    if (error instanceof z.ZodError) {
      res.status(400).json({ error: 'Invalid input', details: error.errors });
      return;
    }
    console.error('Error updating proxy:', error);
    res.status(500).json({ error: 'Failed to update proxy' });
  }
});

// DELETE /admin/proxies/:id - Delete proxy
router.delete('/:id', async (req: Request, res: Response) => {
  try {
    const deleted = await proxyService.deleteProxy(req.params.id);

    if (!deleted) {
      res.status(404).json({ error: 'Proxy not found' });
      return;
    }

    res.json({ deleted: true, id: req.params.id });
  } catch (error) {
    console.error('Error deleting proxy:', error);
    res.status(500).json({ error: 'Failed to delete proxy' });
  }
});

// GET /admin/proxies/:id/keys - List key bindings
router.get('/:id/keys', async (req: Request, res: Response) => {
  try {
    const proxy = await proxyService.getProxy(req.params.id);
    if (!proxy) {
      res.status(404).json({ error: 'Proxy not found' });
      return;
    }

    const bindings = await proxyService.getProxyBindings(req.params.id);
    res.json({ proxyId: req.params.id, bindings });
  } catch (error) {
    console.error('Error listing bindings:', error);
    res.status(500).json({ error: 'Failed to list bindings' });
  }
});

// POST /admin/proxies/:id/keys - Bind key to proxy
router.post('/:id/keys', async (req: Request, res: Response) => {
  try {
    const input = bindKeySchema.parse(req.body);
    const binding = await proxyService.bindKeyToProxy(
      req.params.id,
      input.factoryKeyId,
      input.priority
    );

    res.status(201).json(binding);
  } catch (error) {
    if (error instanceof z.ZodError) {
      res.status(400).json({ error: 'Invalid input', details: error.errors });
      return;
    }
    if (error instanceof Error) {
      if (error.message.includes('not found')) {
        res.status(404).json({ error: error.message });
        return;
      }
      if (error.message.includes('Maximum') || error.message.includes('already')) {
        res.status(400).json({ error: error.message });
        return;
      }
    }
    console.error('Error binding key:', error);
    res.status(500).json({ error: 'Failed to bind key' });
  }
});

// PATCH /admin/proxies/:id/keys/:keyId - Update binding (priority or isActive)
router.patch('/:id/keys/:keyId', async (req: Request, res: Response) => {
  try {
    const input = updateBindingSchema.parse(req.body);
    const binding = await proxyService.updateBinding(
      req.params.id,
      req.params.keyId,
      { priority: input.priority, isActive: input.isActive }
    );

    if (!binding) {
      res.status(404).json({ error: 'Binding not found' });
      return;
    }

    res.json(binding);
  } catch (error) {
    if (error instanceof z.ZodError) {
      res.status(400).json({ error: 'Invalid input', details: error.errors });
      return;
    }
    console.error('Error updating binding:', error);
    res.status(500).json({ error: 'Failed to update binding' });
  }
});

// DELETE /admin/proxies/:id/keys/:keyId - Unbind key
router.delete('/:id/keys/:keyId', async (req: Request, res: Response) => {
  try {
    const deleted = await proxyService.unbindKeyFromProxy(req.params.id, req.params.keyId);

    if (!deleted) {
      res.status(404).json({ error: 'Binding not found' });
      return;
    }

    res.json({ deleted: true, proxyId: req.params.id, factoryKeyId: req.params.keyId });
  } catch (error) {
    console.error('Error unbinding key:', error);
    res.status(500).json({ error: 'Failed to unbind key' });
  }
});

// GET /admin/proxies/:id/health - Get health logs
router.get('/:id/health', async (req: Request, res: Response) => {
  try {
    const proxy = await proxyService.getProxy(req.params.id);
    if (!proxy) {
      res.status(404).json({ error: 'Proxy not found' });
      return;
    }

    const limit = parseInt(req.query.limit as string) || 100;
    const logs = await proxyService.getProxyHealthLogs(req.params.id, limit);
    
    res.json({ proxyId: req.params.id, logs });
  } catch (error) {
    console.error('Error getting health logs:', error);
    res.status(500).json({ error: 'Failed to get health logs' });
  }
});

export default router;
