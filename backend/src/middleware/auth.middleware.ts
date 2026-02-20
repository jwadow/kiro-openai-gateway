import { Request, Response, NextFunction } from 'express';
import { authService } from '../services/auth.service.js';
import { userRepository } from '../repositories/user.repository.js';
import { verifyPassword } from '../models/user-new.model.js';
import { JwtPayload } from '../dtos/auth.dto.js';

declare global {
  namespace Express {
    interface Request {
      user?: JwtPayload;
    }
  }
}

const failedAttempts: Map<string, { count: number; blockedUntil: number }> = new Map();

export async function authMiddleware(req: Request, res: Response, next: NextFunction): Promise<void> {
  const clientIP = req.ip || req.socket.remoteAddress || 'unknown';
  
  const attempt = failedAttempts.get(clientIP);
  if (attempt && attempt.blockedUntil > Date.now()) {
    const retryAfter = Math.ceil((attempt.blockedUntil - Date.now()) / 1000);
    res.status(429).json({
      error: 'Too many failed authentication attempts',
      retry_after: retryAfter,
    });
    return;
  }
  
  const authHeader = req.headers.authorization;
  if (!authHeader) {
    res.status(401).json({ 
      error: 'Authentication required',
      hint: 'Use Authorization: Bearer <token>'
    });
    return;
  }

  // JWT Bearer token
  if (authHeader.startsWith('Bearer ')) {
    const token = authHeader.substring(7);
    try {
      const payload = authService.verifyToken(token);
      req.user = payload;
      failedAttempts.delete(clientIP);
      next();
      return;
    } catch (error: any) {
      res.status(401).json({ error: error.message });
      return;
    }
  }

  // Basic Auth (backward compatible, deprecated)
  if (authHeader.startsWith('Basic ')) {
    const base64Credentials = authHeader.substring(6);
    const credentials = Buffer.from(base64Credentials, 'base64').toString('utf-8');
    const [username, password] = credentials.split(':');

    if (username && password) {
      try {
        const user = await userRepository.findById(username);
        if (user && user.isActive && verifyPassword(password, user.passwordHash, user.passwordSalt)) {
          await userRepository.updateLastLogin(username);
          req.user = { username, role: user.role };
          failedAttempts.delete(clientIP);
          next();
          return;
        }
      } catch (error) {
        console.error('Auth error:', error);
      }
    }
  }

  recordFailedAttempt(clientIP);
  res.status(401).json({ 
    error: 'Invalid or expired token',
    hint: 'Please login again to get a new token'
  });
}

function recordFailedAttempt(ip: string): void {
  const attempt = failedAttempts.get(ip) || { count: 0, blockedUntil: 0 };
  attempt.count++;

  if (attempt.count >= 10) {
    attempt.blockedUntil = Date.now() + 5 * 60 * 1000;
    attempt.count = 0;
  }

  failedAttempts.set(ip, attempt);
}

setInterval(() => {
  const now = Date.now();
  for (const [ip, attempt] of failedAttempts.entries()) {
    if (attempt.blockedUntil < now && attempt.count === 0) {
      failedAttempts.delete(ip);
    }
  }
}, 60000);

export async function jwtAuth(req: Request, res: Response, next: NextFunction): Promise<void> {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    res.status(401).json({ error: 'Authentication required' });
    return;
  }

  const token = authHeader.substring(7);
  try {
    const payload = authService.verifyToken(token);
    req.user = payload;
    next();
  } catch (error: any) {
    res.status(401).json({ error: error.message });
  }
}
