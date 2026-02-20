import { Router, Request, Response } from 'express';
import { paymentService, SepayWebhookPayload } from '../services/payment.service.js';
import { jwtAuth } from '../middleware/auth.middleware.js';
import { MIN_CREDITS, MAX_CREDITS, VND_RATE_NEW, VALIDITY_DAYS } from '../models/payment.model.js';

const router = Router();

// Middleware to verify SePay webhook API key
function verifySepayWebhook(req: Request, res: Response, next: Function) {
  const authHeader = req.headers['authorization'];
  const expectedApiKey = process.env.SEPAY_API_KEY;

  if (!expectedApiKey) {
    console.error('[Payment Webhook] SEPAY_API_KEY not configured');
    return res.status(500).json({ error: 'Webhook not configured' });
  }

  if (!authHeader || authHeader !== `Apikey ${expectedApiKey}`) {
    console.log('[Payment Webhook] Invalid authorization header');
    return res.status(401).json({ error: 'Unauthorized' });
  }

  next();
}

// POST /api/payment/checkout - Create payment and get QR code
router.post('/checkout', jwtAuth, async (req: Request, res: Response) => {
  try {
    const username = (req as any).user?.username;
    if (!username) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const { credits, discordId } = req.body as { credits?: string | number; discordId?: string };

    // Parse credits amount
    const creditsAmount = typeof credits === 'string' ? parseInt(credits, 10) : credits;

    if (!creditsAmount || !Number.isInteger(creditsAmount) || creditsAmount < MIN_CREDITS || creditsAmount > MAX_CREDITS) {
      return res.status(400).json({ error: `Invalid amount. Must be between $${MIN_CREDITS} and $${MAX_CREDITS}` });
    }

    // Use the logged-in username as transfer content
    const result = await paymentService.createCheckout(username, creditsAmount, discordId, username);

    res.json({
      paymentId: result.paymentId,
      orderCode: result.orderCode,
      qrCodeUrl: result.qrCodeUrl,
      amount: result.amount,
      credits: result.credits,
      expiresAt: result.expiresAt,
    });
  } catch (error: any) {
    console.error('[Payment Checkout Error]', error);
    res.status(400).json({ error: error.message });
  }
});

// POST /api/payment/webhook - Handle SePay webhook
router.post('/webhook', verifySepayWebhook, async (req: Request, res: Response) => {
  try {
    const payload = req.body as SepayWebhookPayload;

    console.log('[Payment Webhook] Received:', JSON.stringify(payload));

    const result = await paymentService.processWebhook(payload);

    // Always return 200 to acknowledge receipt
    res.status(200).json(result);
  } catch (error: any) {
    console.error('[Payment Webhook Error]', error);
    // Still return 200 to prevent SePay from retrying
    res.status(200).json({ processed: false, message: error.message });
  }
});

// GET /api/payment/user-stats - Get user's payment statistics
router.get('/user-stats', jwtAuth, async (req: Request, res: Response) => {
  try {
    const username = (req as any).user?.username;
    if (!username) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const stats = await paymentService.getUserPaymentStats(username);
    res.json(stats);
  } catch (error: any) {
    console.error('[Payment User Stats Error]', error);
    res.status(500).json({ error: error.message });
  }
});

// GET /api/payment/history-paginated - Get paginated payment history with filters
router.get('/history-paginated', jwtAuth, async (req: Request, res: Response) => {
  try {
    const username = (req as any).user?.username;
    if (!username) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const { page, limit, status, from, to } = req.query;

    const result = await paymentService.getPaymentHistoryPaginated(username, {
      page: page ? parseInt(page as string, 10) : undefined,
      limit: limit ? parseInt(limit as string, 10) : undefined,
      status: status as string,
      from: from as string,
      to: to as string,
    });

    res.json({
      payments: result.payments.map(p => ({
        id: p._id,
        orderCode: p.orderCode,
        credits: p.credits,
        amount: p.amount,
        status: p.status,
        createdAt: p.createdAt,
        completedAt: p.completedAt,
      })),
      total: result.total,
      page: result.page,
      totalPages: result.totalPages,
    });
  } catch (error: any) {
    console.error('[Payment History Paginated Error]', error);
    res.status(500).json({ error: error.message });
  }
});

// GET /api/payment/:id/status - Poll payment status
router.get('/:id/status', jwtAuth, async (req: Request, res: Response) => {
  try {
    const username = (req as any).user?.username;
    if (!username) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const { id } = req.params;
    const status = await paymentService.getPaymentStatus(id, username);

    if (!status) {
      return res.status(404).json({ error: 'Payment not found' });
    }

    res.json(status);
  } catch (error: any) {
    console.error('[Payment Status Error]', error);
    res.status(500).json({ error: error.message });
  }
});

// GET /api/payment/history - Get user's payment history
router.get('/history', jwtAuth, async (req: Request, res: Response) => {
  try {
    const username = (req as any).user?.username;
    if (!username) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const payments = await paymentService.getPaymentHistory(username);

    res.json({
      payments: payments.map(p => ({
        id: p._id,
        orderCode: p.orderCode,
        credits: p.credits,
        amount: p.amount,
        status: p.status,
        createdAt: p.createdAt,
        completedAt: p.completedAt,
      })),
    });
  } catch (error: any) {
    console.error('[Payment History Error]', error);
    res.status(500).json({ error: error.message });
  }
});

// GET /api/payment/config - Get payment configuration (public)
router.get('/config', (_req: Request, res: Response) => {
  res.json({
    minCredits: MIN_CREDITS,
    maxCredits: MAX_CREDITS,
    vndRate: VND_RATE_NEW,
    validityDays: VALIDITY_DAYS,
    currency: 'VND',
    features: ['All AI models', 'Valid for 7 days', '1:1 Warranty', 'Priority support'],
  });
});

export default router;
