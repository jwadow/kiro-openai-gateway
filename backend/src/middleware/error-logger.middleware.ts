import { Request, Response, NextFunction } from 'express';
import { ErrorLog } from '../models/error-log.model.js';

// Sanitize sensitive data from request/response body (recursive, max 3 levels)
function sanitizeBody(body: any, depth: number = 0): any {
  if (!body || depth > 3) return body;
  if (typeof body !== 'object') return body;
  if (Array.isArray(body)) {
    return body.map(item => sanitizeBody(item, depth + 1));
  }
  
  const sanitized = { ...body };
  const sensitiveFields = [
    'password', 'token', 'apiKey', 'secret', 'authorization', 
    'api_key', 'accessToken', 'refreshToken', 'credential', 
    'privateKey', 'private_key', 'sessionToken', 'session_token'
  ];
  
  for (const key of Object.keys(sanitized)) {
    const lowerKey = key.toLowerCase();
    // Check if key matches sensitive field patterns
    if (sensitiveFields.some(f => lowerKey.includes(f.toLowerCase()))) {
      sanitized[key] = '[REDACTED]';
    } else if (typeof sanitized[key] === 'object' && sanitized[key] !== null) {
      // Recursively sanitize nested objects
      sanitized[key] = sanitizeBody(sanitized[key], depth + 1);
    }
  }
  return sanitized;
}

// Get safe headers (exclude auth)
function getSafeHeaders(headers: any): Record<string, string> {
  const safe: Record<string, string> = {};
  const allowedHeaders = ['content-type', 'accept', 'origin', 'referer', 'x-request-id', 'user-agent'];
  for (const h of allowedHeaders) {
    if (headers[h]) safe[h] = String(headers[h]);
  }
  return safe;
}

// Classify error type from status code
function classifyError(statusCode: number): string {
  if (statusCode === 400) return 'validation_error';
  if (statusCode === 401) return 'authentication_error';
  if (statusCode === 403) return 'authorization_error';
  if (statusCode === 404) return 'not_found';
  if (statusCode === 409) return 'conflict_error';
  if (statusCode === 429) return 'rate_limit_error';
  if (statusCode >= 500) return 'server_error';
  return 'client_error';
}

// Get client IP from request
function getClientIp(req: Request): string {
  const forwarded = req.headers['x-forwarded-for'];
  if (typeof forwarded === 'string') {
    return forwarded.split(',')[0].trim();
  }
  const realIp = req.headers['x-real-ip'];
  if (typeof realIp === 'string') {
    return realIp;
  }
  return req.ip || req.socket?.remoteAddress || 'unknown';
}

export function errorLoggerMiddleware(req: Request, res: Response, next: NextFunction) {
  const startTime = Date.now();
  
  // Store original json method
  const originalJson = res.json.bind(res);
  
  // Override json method to intercept error responses
  res.json = function(body: any) {
    const statusCode = res.statusCode;
    
    // Only log 4xx and 5xx errors
    if (statusCode >= 400) {
      const latencyMs = Date.now() - startTime;
      
      // Log async - don't block response
      setImmediate(async () => {
        try {
          await ErrorLog.create({
            source: 'backend',
            method: req.method,
            path: req.path,
            endpoint: req.originalUrl,
            userId: (req as any).user?.username,
            clientIp: getClientIp(req),
            userAgent: req.headers['user-agent'],
            statusCode,
            errorType: classifyError(statusCode),
            errorMessage: body?.error || body?.message || 'Unknown error',
            errorDetails: body?.details,
            requestHeaders: getSafeHeaders(req.headers),
            requestBody: sanitizeBody(req.body),
            responseBody: sanitizeBody(body),
            latencyMs,
          });
        } catch (err) {
          console.error('[ErrorLogger] Failed to log error:', err);
        }
      });
    }
    
    return originalJson(body);
  };
  
  next();
}
