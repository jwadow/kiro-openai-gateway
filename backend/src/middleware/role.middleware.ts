import { Request, Response, NextFunction } from 'express';

type Role = 'admin' | 'user';

export function requireRole(...allowedRoles: Role[]) {
  return (req: Request, res: Response, next: NextFunction): void => {
    if (!req.user) {
      res.status(401).json({ error: 'Authentication required' });
      return;
    }

    const userRole = req.user.role as Role;
    
    if (!allowedRoles.includes(userRole)) {
      res.status(403).json({ 
        error: 'Insufficient permissions',
        required_roles: allowedRoles,
        your_role: userRole
      });
      return;
    }

    next();
  };
}

export function requireAdmin(req: Request, res: Response, next: NextFunction): void {
  if (!req.user) {
    res.status(401).json({ error: 'Authentication required' });
    return;
  }

  if (req.user.role !== 'admin') {
    res.status(403).json({ 
      error: 'Insufficient permissions',
      hint: 'Admin role required'
    });
    return;
  }

  next();
}

export function allowReadOnly(req: Request, res: Response, next: NextFunction): void {
  if (!req.user) {
    res.status(401).json({ error: 'Authentication required' });
    return;
  }

  // Admin can do everything
  if (req.user.role === 'admin') {
    next();
    return;
  }

  // User can only read (GET requests)
  if (req.method === 'GET') {
    next();
    return;
  }

  res.status(403).json({ 
    error: 'Insufficient permissions',
    hint: 'User role can only perform read operations'
  });
}
