import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import { connectDB } from './db/mongodb.js';
import { authMiddleware } from './middleware/auth.middleware.js';
import { errorLoggerMiddleware } from './middleware/error-logger.middleware.js';
import authRoutes from './routes/auth.routes.js';
import adminRoutes from './routes/admin.routes.js';
import usageRoutes from './routes/usage.js';
import proxyRoutes from './routes/proxy.js';
import statusRoutes from './routes/status.js';
import userRoutes from './routes/user.routes.js';
import paymentRoutes from './routes/payment.routes.js';
import modelsRoutes from './routes/models.routes.js';
import friendKeyRoutes from './routes/friend-key.routes.js';
import openhandsRoutes from './routes/openhands.routes.js';
import ohmygptRoutes from './routes/ohmygpt.routes.js';
import webhookRoutes from './routes/webhook.routes.js';
import { expirationSchedulerService } from './services/expiration-scheduler.service.js';

const app = express();
const PORT = parseInt(process.env.BACKEND_PORT || '3000', 10);

// Middleware
app.use(cors({
  origin: [
    'http://localhost:3000',
    'http://localhost:3001',
    'https://trollllm.xyz',
    'https://www.trollllm.xyz',
    'https://api.trollllm.xyz',
    'https://chat.trollllm.xyz',
  ],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'x-api-key'],
}));
app.use(express.json());
app.use(errorLoggerMiddleware);

// Health check
app.get('/health', (_req, res) => {
  res.json({
    status: 'healthy',
    service: 'fproxy-backend',
    timestamp: new Date().toISOString(),
  });
});

// Public API routes
app.use('/api', usageRoutes);
app.use('/api/status', statusRoutes);
app.use('/api/models', modelsRoutes);

// Auth routes (public)
app.use('/api', authRoutes);

// User routes (protected with JWT)
app.use('/api/user', userRoutes);
// app.use('/api/user/friend-key', friendKeyRoutes); // TEMPORARILY DISABLED

// Payment routes (mixed: some public, some protected)
app.use('/api/payment', paymentRoutes);

// Admin routes (protected with JWT)
app.use('/admin', authMiddleware, adminRoutes);
app.use('/admin/proxies', authMiddleware, proxyRoutes);
app.use('/admin/openhands', authMiddleware, openhandsRoutes);
app.use('/admin/ohmygpt', authMiddleware, ohmygptRoutes);

// Webhook routes (no JWT auth - uses X-Webhook-Secret header)
app.use('/webhook', webhookRoutes);

// Root
app.get('/', (_req, res) => {
  res.json({
    service: 'F-Proxy Backend',
    version: '2.0.0',
    endpoints: {
      public: [
        'GET /health',
        'GET /api/usage?key=xxx',
        'GET /api/status',
        'POST /api/login',
        'POST /api/register',
      ],
      user: [
        'GET /api/user/me',
        'GET /api/user/api-key',
        'POST /api/user/api-key/rotate',
        'GET /api/user/billing',
        'GET /api/user/friend-key',
        'POST /api/user/friend-key',
        'POST /api/user/friend-key/rotate',
        'DELETE /api/user/friend-key',
        'PUT /api/user/friend-key/limits',
        'GET /api/user/friend-key/usage',
      ],
      admin: [
        'GET /admin/keys',
        'POST /admin/keys',
        'GET /admin/keys/:id',
        'PATCH /admin/keys/:id',
        'DELETE /admin/keys/:id',
        'POST /admin/keys/:id/reset',
        'GET /admin/metrics',
        'GET /admin/proxies',
        'POST /admin/proxies',
        'PATCH /admin/proxies/:id',
        'DELETE /admin/proxies/:id',
      ],
    },
    auth: {
      login: 'POST /api/login { "username": "...", "password": "..." }',
      register: 'POST /api/register { "username": "...", "password": "...", "role": "user|admin" }',
      usage: 'Authorization: Bearer <token>',
    },
    roles: {
      admin: 'Full access to all endpoints',
      user: 'Read-only access to admin endpoints',
    },
  });
});

// 404 handler
app.use((_req, res) => {
  res.status(404).json({ error: 'Not found' });
});

// Error handler
app.use((err: Error, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
  console.error('Unhandled error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

// Start server
async function main() {
  try {
    await connectDB();

    // Initialize expiration scheduler after DB connection
    const { scheduled, resetImmediately, cleanedUp } = await expirationSchedulerService.init();
    console.log(`[Startup] Expiration scheduler: ${scheduled} scheduled, ${resetImmediately} reset, ${cleanedUp} cleaned up`);

    app.listen(PORT, () => {
      console.log(`F-Proxy Backend started at http://localhost:${PORT}`);
      console.log(`API Usage: GET /api/usage?key=xxx`);
      console.log(`Admin API: /admin/*`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

main();
