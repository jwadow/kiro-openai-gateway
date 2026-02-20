import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { User, verifyPassword, hashPassword } from '../db/mongodb.js';

const JWT_SECRET = process.env.ADMIN_SECRET_KEY || 'change-this-to-random-secret';
const JWT_EXPIRES_IN = '24h';

interface JwtPayload {
  username: string;
  role: string;
}

// Simple in-memory rate limiting for failed auth attempts
const failedAttempts: Map<string, { count: number; blockedUntil: number }> = new Map();

export async function adminAuth(req: Request, res: Response, next: NextFunction): Promise<void> {
  const clientIP = req.ip || req.socket.remoteAddress || 'unknown';
  
  // Check if IP is blocked
  const attempt = failedAttempts.get(clientIP);
  if (attempt && attempt.blockedUntil > Date.now()) {
    const retryAfter = Math.ceil((attempt.blockedUntil - Date.now()) / 1000);
    res.status(429).json({
      error: 'Too many failed authentication attempts',
      retry_after: retryAfter,
    });
    return;
  }
  
  // Check for auth headers
  const authHeader = req.headers.authorization;
  if (!authHeader) {
    res.status(401).json({ 
      error: 'Authentication required',
      hint: 'Use Bearer token from login response'
    });
    return;
  }

  // Check Bearer Token (JWT)
  if (authHeader.startsWith('Bearer ')) {
    const token = authHeader.substring(7);
    try {
      const decoded = jwt.verify(token, JWT_SECRET) as JwtPayload;
      // Attach user info to request
      (req as any).user = decoded;
      failedAttempts.delete(clientIP);
      next();
      return;
    } catch (error) {
      // Token invalid or expired
    }
  }

  // Check Basic Auth (username:password) - backward compatible
  if (authHeader.startsWith('Basic ')) {
    const base64Credentials = authHeader.substring(6);
    const credentials = Buffer.from(base64Credentials, 'base64').toString('utf-8');
    const [username, password] = credentials.split(':');

    if (username && password) {
      try {
        const user = await User.findById(username);
        if (user && user.isActive && verifyPassword(password, user.passwordHash, user.passwordSalt)) {
          await User.updateOne({ _id: username }, { lastLoginAt: new Date() });
          (req as any).user = { username, role: user.role };
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

// Login endpoint handler
export async function loginHandler(req: Request, res: Response): Promise<void> {
  const { username, password } = req.body;

  if (!username || !password) {
    res.status(400).json({ error: 'Username and password required' });
    return;
  }

  try {
    const user = await User.findById(username);
    if (!user || !user.isActive || !verifyPassword(password, user.passwordHash, user.passwordSalt)) {
      res.status(401).json({ error: 'Invalid credentials' });
      return;
    }

    // Create JWT token
    const payload: JwtPayload = { username, role: user.role };
    const token = jwt.sign(payload, JWT_SECRET, { expiresIn: JWT_EXPIRES_IN });

    // Update last login
    await User.updateOne({ _id: username }, { lastLoginAt: new Date() });

    res.json({
      token,
      username,
      role: user.role,
      expires_in: JWT_EXPIRES_IN,
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ error: 'Login failed' });
  }
}

// Register endpoint handler
export async function registerHandler(req: Request, res: Response): Promise<void> {
  const { username, password, role } = req.body;

  if (!username || !password) {
    res.status(400).json({ error: 'Username and password required' });
    return;
  }

  if (username.length < 3 || username.length > 50) {
    res.status(400).json({ error: 'Username must be 3-50 characters' });
    return;
  }

  if (password.length < 6) {
    res.status(400).json({ error: 'Password must be at least 6 characters' });
    return;
  }

  try {
    // Check if user already exists
    const existingUser = await User.findById(username);
    if (existingUser) {
      res.status(409).json({ error: 'Username already exists' });
      return;
    }

    // Hash password
    const { hash, salt } = hashPassword(password);

    // Create user
    await User.create({
      _id: username,
      passwordHash: hash,
      passwordSalt: salt,
      role: role === 'admin' ? 'admin' : 'viewer',
      isActive: true,
    });

    // Generate token for immediate login
    const payload: JwtPayload = { username, role: role === 'admin' ? 'admin' : 'viewer' };
    const token = jwt.sign(payload, JWT_SECRET, { expiresIn: JWT_EXPIRES_IN });

    res.status(201).json({
      message: 'User registered successfully',
      token,
      username,
      role: payload.role,
      expires_in: JWT_EXPIRES_IN,
    });
  } catch (error) {
    console.error('Register error:', error);
    res.status(500).json({ error: 'Registration failed' });
  }
}

function recordFailedAttempt(ip: string): void {
  const attempt = failedAttempts.get(ip) || { count: 0, blockedUntil: 0 };
  attempt.count++;

  // Block for 5 minutes after 10 failed attempts
  if (attempt.count >= 10) {
    attempt.blockedUntil = Date.now() + 5 * 60 * 1000;
    attempt.count = 0;
  }

  failedAttempts.set(ip, attempt);
}

// Cleanup old entries periodically
setInterval(() => {
  const now = Date.now();
  for (const [ip, attempt] of failedAttempts.entries()) {
    if (attempt.blockedUntil < now && attempt.count === 0) {
      failedAttempts.delete(ip);
    }
  }
}, 60000);
