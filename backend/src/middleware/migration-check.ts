import { Request, Response, NextFunction } from 'express';
import { userNewRepository } from '../repositories/user-new.repository.js';
import { migrationService } from '../services/migration.service.js';

/**
 * Middleware to check if user has migrated to the new billing rate.
 * Blocks API access for non-migrated users (existing users only).
 * Auto-migrates users with zero credits.
 * Admins bypass this check.
 */
export async function checkMigration(req: Request, res: Response, next: NextFunction) {
  try {
    const username = (req as any).user?.username;
    const role = (req as any).user?.role;

    // Bypass for admins
    if (role === 'admin') {
      return next();
    }

    if (!username) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    // Check migration status
    const hasMigrated = await userNewRepository.getMigrationStatus(username);

    if (!hasMigrated) {
      // Attempt auto-migration for users with zero credits
      const autoMigrated = await migrationService.autoMigrateIfZeroCredits(username);

      if (autoMigrated) {
        // User was auto-migrated, allow request to proceed
        return next();
      }

      // User has credits > 0, block the request
      const dashboardUrl = process.env.FRONTEND_URL || 'https://trollllm.xyz';
      return res.status(403).json({
        error: 'Migration required',
        message: 'You need to migrate your account to the new billing rate to continue using the API.',
        dashboardUrl: `${dashboardUrl}/dashboard`,
      });
    }

    next();
  } catch (error: any) {
    res.status(500).json({ error: 'Internal server error' });
  }
}
