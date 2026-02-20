import { Request, Response, NextFunction } from 'express';

/**
 * Webhook authentication middleware.
 * Validates requests using X-Webhook-Secret header against OPENHANDS_WEBHOOK_SECRET env var.
 * Used for machine-to-machine communication (no JWT).
 */
export function webhookAuthMiddleware(req: Request, res: Response, next: NextFunction): void {
  const webhookSecret = process.env.OPENHANDS_WEBHOOK_SECRET;
  
  // Validate that webhook secret is configured
  if (!webhookSecret) {
    console.error('[Webhook] OPENHANDS_WEBHOOK_SECRET not configured');
    res.status(500).json({ error: 'Webhook authentication not configured' });
    return;
  }

  const providedSecret = req.headers['x-webhook-secret'];

  // Check if secret header is provided
  if (!providedSecret) {
    res.status(401).json({ 
      error: 'Webhook authentication required',
      hint: 'Provide X-Webhook-Secret header'
    });
    return;
  }

  // Validate the secret
  if (providedSecret !== webhookSecret) {
    res.status(401).json({ error: 'Invalid webhook secret' });
    return;
  }

  next();
}
