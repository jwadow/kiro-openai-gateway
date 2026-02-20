import { Router, Request, Response } from 'express';
import { Proxy, ProxyKeyBinding, ProxyHealthLog } from '../db/mongodb.js';

const router = Router();

// GET /api/status - Public status endpoint
router.get('/', async (_req: Request, res: Response) => {
  try {
    const proxies = await Proxy.find({ isActive: true }).sort({ _id: 1 });
    
    // Get binding counts for each proxy
    const proxyStatuses = await Promise.all(proxies.map(async (proxy) => {
      const bindingCount = await ProxyKeyBinding.countDocuments({ 
        proxyId: proxy._id, 
        isActive: true 
      });
      
      return {
        id: proxy._id,
        name: proxy.name,
        type: proxy.type,
        status: proxy.status,
        latencyMs: proxy.lastLatencyMs,
        lastCheckedAt: proxy.lastCheckedAt,
        lastError: proxy.status === 'unhealthy' ? proxy.lastError : undefined,
        keysCount: bindingCount,
        maxKeys: 2,
      };
    }));

    // Calculate overall status
    const healthyCount = proxyStatuses.filter(p => p.status === 'healthy').length;
    const totalCount = proxyStatuses.length;
    
    let overallStatus: 'healthy' | 'degraded' | 'down' | 'unknown';
    if (totalCount === 0) {
      overallStatus = 'unknown';
    } else if (healthyCount === totalCount) {
      overallStatus = 'healthy';
    } else if (healthyCount === 0) {
      overallStatus = 'down';
    } else {
      overallStatus = 'degraded';
    }

    // Get last health check time
    const lastLog = await ProxyHealthLog.findOne().sort({ checkedAt: -1 });

    res.json({
      status: overallStatus,
      summary: {
        total: totalCount,
        healthy: healthyCount,
        unhealthy: totalCount - healthyCount,
      },
      lastCheckAt: lastLog?.checkedAt || null,
      proxies: proxyStatuses,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error getting status:', error);
    res.status(500).json({ error: 'Failed to get status' });
  }
});

export default router;
