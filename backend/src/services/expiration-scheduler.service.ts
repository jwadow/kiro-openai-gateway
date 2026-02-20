import { UserNew, IUserNew } from '../models/user-new.model.js';
import { creditsResetLogRepository } from '../repositories/credits-reset-log.repository.js';
import { ResetTrigger } from '../models/credits-reset-log.model.js';

// In-memory map of scheduled timeouts
const scheduledExpirations = new Map<string, NodeJS.Timeout>();
// Separate map for creditsNew (OpenHands) expirations
const scheduledExpirationsNew = new Map<string, NodeJS.Timeout>();

// Max safe timeout (24.8 days in ms) - setTimeout has 32-bit limit
const MAX_TIMEOUT_MS = 2147483647;

export class ExpirationSchedulerService {
  private static instance: ExpirationSchedulerService;

  private constructor() {}

  static getInstance(): ExpirationSchedulerService {
    if (!ExpirationSchedulerService.instance) {
      ExpirationSchedulerService.instance = new ExpirationSchedulerService();
    }
    return ExpirationSchedulerService.instance;
  }

  /**
   * Initialize scheduler on backend start
   * - Query all users with credits > 0 and expiresAt set
   * - Query all users with creditsNew > 0 and expiresAtNew set
   * - Schedule timeout for each or reset immediately if already expired
   * - Also cleanup expired users with credits = 0 but still have expiresAt set
   */
  async init(): Promise<{ scheduled: number; scheduledNew: number; resetImmediately: number; resetImmediatelyNew: number; cleanedUp: number }> {
    console.log('[ExpirationScheduler] Initializing...');

    // 1. Handle users with credits > 0 (OhMyGPT)
    const usersWithCredits = await UserNew.find({
      credits: { $gt: 0 },
      expiresAt: { $ne: null },
    }).lean();

    let scheduled = 0;
    let resetImmediately = 0;

    for (const user of usersWithCredits) {
      if (!user.expiresAt) continue;

      const timeUntilExpiry = new Date(user.expiresAt).getTime() - Date.now();

      if (timeUntilExpiry <= 0) {
        // Already expired - reset immediately
        await this.resetAndLog(user._id, 'auto');
        resetImmediately++;
      } else {
        // Schedule for future
        this.scheduleExpiration(user._id, user.expiresAt);
        scheduled++;
      }
    }

    // 2. Handle users with creditsNew > 0 (OpenHands)
    const usersWithCreditsNew = await UserNew.find({
      creditsNew: { $gt: 0 },
      expiresAtNew: { $ne: null },
    }).lean();

    let scheduledNew = 0;
    let resetImmediatelyNew = 0;

    for (const user of usersWithCreditsNew) {
      if (!user.expiresAtNew) continue;

      const timeUntilExpiry = new Date(user.expiresAtNew).getTime() - Date.now();

      if (timeUntilExpiry <= 0) {
        // Already expired - reset immediately
        await this.resetAndLogNew(user._id, 'auto');
        resetImmediatelyNew++;
      } else {
        // Schedule for future
        this.scheduleExpirationNew(user._id, user.expiresAtNew);
        scheduledNew++;
      }
    }

    // 3. Cleanup expired users with credits = 0 but still have expiresAt set
    const cleanedUp = await this.cleanupExpiredZeroCredits();

    console.log(`[ExpirationScheduler] Init complete: credits=${scheduled} scheduled/${resetImmediately} reset, creditsNew=${scheduledNew} scheduled/${resetImmediatelyNew} reset, ${cleanedUp} cleaned up`);
    return { scheduled, scheduledNew, resetImmediately, resetImmediatelyNew, cleanedUp };
  }

  /**
   * Cleanup users with credits = 0 but still have expired expiresAt
   * Also cleanup creditsNew = 0 but still have expired expiresAtNew
   * Resets purchasedAt/expiresAt and purchasedAtNew/expiresAtNew to null without logging (no credits lost)
   */
  async cleanupExpiredZeroCredits(): Promise<number> {
    const now = new Date();

    // Cleanup credits (OhMyGPT)
    const result1 = await UserNew.updateMany(
      {
        credits: { $lte: 0 },
        expiresAt: { $ne: null, $lt: now },
      },
      {
        $set: {
          purchasedAt: null,
          expiresAt: null,
        },
      }
    );

    // Cleanup creditsNew (OpenHands)
    const result2 = await UserNew.updateMany(
      {
        creditsNew: { $lte: 0 },
        expiresAtNew: { $ne: null, $lt: now },
      },
      {
        $set: {
          purchasedAtNew: null,
          expiresAtNew: null,
        },
      }
    );

    const totalCleaned = result1.modifiedCount + result2.modifiedCount;
    if (totalCleaned > 0) {
      console.log(`[ExpirationScheduler] Cleaned up ${result1.modifiedCount} expired credits, ${result2.modifiedCount} expired creditsNew`);
    }

    return totalCleaned;
  }

  /**
   * Schedule expiration for a user
   * Cancels existing schedule if any
   */
  scheduleExpiration(username: string, expiresAt: Date): void {
    // Cancel existing timeout if any
    this.cancelExpiration(username);

    const timeUntilExpiry = new Date(expiresAt).getTime() - Date.now();

    if (timeUntilExpiry <= 0) {
      // Already expired - reset immediately
      console.log(`[ExpirationScheduler] ${username} already expired, resetting now`);
      this.resetAndLog(username, 'auto');
      return;
    }

    // Handle long timeouts (> 24.8 days)
    const actualTimeout = Math.min(timeUntilExpiry, MAX_TIMEOUT_MS);
    const needsReschedule = timeUntilExpiry > MAX_TIMEOUT_MS;

    const timeout = setTimeout(async () => {
      if (needsReschedule) {
        // Reschedule for remaining time
        const remaining = timeUntilExpiry - MAX_TIMEOUT_MS;
        const newExpiresAt = new Date(Date.now() + remaining);
        this.scheduleExpiration(username, newExpiresAt);
      } else {
        // Actually expired
        await this.resetAndLog(username, 'auto');
      }
    }, actualTimeout);

    scheduledExpirations.set(username, timeout);

    const expiresIn = Math.round(timeUntilExpiry / 1000 / 60); // minutes
    console.log(`[ExpirationScheduler] Scheduled ${username} to expire in ${expiresIn} minutes`);
  }

  /**
   * Cancel scheduled expiration for a user
   */
  cancelExpiration(username: string): boolean {
    const existing = scheduledExpirations.get(username);
    if (existing) {
      clearTimeout(existing);
      scheduledExpirations.delete(username);
      return true;
    }
    return false;
  }

  /**
   * Schedule expiration for creditsNew (OpenHands)
   * Cancels existing schedule if any (both old credits and creditsNew timers)
   */
  scheduleExpirationNew(username: string, expiresAtNew: Date): void {
    // Cancel existing timeout from BOTH maps (important for migration from old code)
    // Old code may have scheduled timer in scheduledExpirations instead of scheduledExpirationsNew
    this.cancelExpiration(username);      // Cancel old credits timer if any
    this.cancelExpirationNew(username);   // Cancel creditsNew timer if any

    const timeUntilExpiry = new Date(expiresAtNew).getTime() - Date.now();

    if (timeUntilExpiry <= 0) {
      // Already expired - reset immediately
      console.log(`[ExpirationScheduler] ${username} creditsNew already expired, resetting now`);
      this.resetAndLogNew(username, 'auto');
      return;
    }

    // Handle long timeouts (> 24.8 days)
    const actualTimeout = Math.min(timeUntilExpiry, MAX_TIMEOUT_MS);
    const needsReschedule = timeUntilExpiry > MAX_TIMEOUT_MS;

    const timeout = setTimeout(async () => {
      if (needsReschedule) {
        // Reschedule for remaining time
        const remaining = timeUntilExpiry - MAX_TIMEOUT_MS;
        const newExpiresAtNew = new Date(Date.now() + remaining);
        this.scheduleExpirationNew(username, newExpiresAtNew);
      } else {
        // Actually expired
        await this.resetAndLogNew(username, 'auto');
      }
    }, actualTimeout);

    scheduledExpirationsNew.set(username, timeout);

    const expiresIn = Math.round(timeUntilExpiry / 1000 / 60); // minutes
    console.log(`[ExpirationScheduler] Scheduled ${username} creditsNew to expire in ${expiresIn} minutes`);
  }

  /**
   * Cancel scheduled expiration for creditsNew
   */
  cancelExpirationNew(username: string): boolean {
    const existing = scheduledExpirationsNew.get(username);
    if (existing) {
      clearTimeout(existing);
      scheduledExpirationsNew.delete(username);
      return true;
    }
    return false;
  }

  /**
   * Reset user credits and log the action
   * Also handles cleanup when credits = 0 but expiresAt is set
   */
  async resetAndLog(username: string, triggeredBy: ResetTrigger, note?: string): Promise<boolean> {
    try {
      // Get user before reset to capture creditsBefore
      const user = await UserNew.findById(username).lean();
      if (!user) {
        console.log(`[ExpirationScheduler] User ${username} not found`);
        return false;
      }

      const creditsBefore = user.credits;
      const expiresAt = user.expiresAt;

      // If credits = 0 and expired, just cleanup without logging
      if (creditsBefore <= 0) {
        if (expiresAt && new Date() > new Date(expiresAt)) {
          await UserNew.findByIdAndUpdate(username, {
            purchasedAt: null,
            expiresAt: null,
          });
          console.log(`[ExpirationScheduler] Cleaned up ${username} (0 credits, expired)`);
        }
        // Clean up schedule if exists
        scheduledExpirations.delete(username);
        return false;
      }

      // Reset credits
      await UserNew.findByIdAndUpdate(username, {
        credits: 0,
        purchasedAt: null,
        expiresAt: null,
      });

      // Log the reset (only when credits > 0)
      await creditsResetLogRepository.create({
        username,
        creditsBefore,
        expiresAt: expiresAt || null,
        resetBy: triggeredBy,
        note,
      });

      // Remove from scheduled map
      scheduledExpirations.delete(username);

      console.log(`[ExpirationScheduler] Reset ${username}: $${creditsBefore.toFixed(2)} credits, triggered by ${triggeredBy}`);
      return true;
    } catch (error) {
      console.error(`[ExpirationScheduler] Error resetting ${username}:`, error);
      return false;
    }
  }

  /**
   * Reset user creditsNew (OpenHands) and log the action
   * Also handles cleanup when creditsNew = 0 but expiresAtNew is set
   */
  async resetAndLogNew(username: string, triggeredBy: ResetTrigger, note?: string): Promise<boolean> {
    try {
      // Get user before reset to capture creditsBefore
      const user = await UserNew.findById(username).lean();
      if (!user) {
        console.log(`[ExpirationScheduler] User ${username} not found`);
        return false;
      }

      const creditsBefore = user.creditsNew || 0;
      const expiresAtNew = user.expiresAtNew;

      // If creditsNew = 0 and expired, just cleanup without logging
      if (creditsBefore <= 0) {
        if (expiresAtNew && new Date() > new Date(expiresAtNew)) {
          await UserNew.findByIdAndUpdate(username, {
            purchasedAtNew: null,
            expiresAtNew: null,
          });
          console.log(`[ExpirationScheduler] Cleaned up ${username} (0 creditsNew, expired)`);
        }
        // Clean up schedule if exists
        scheduledExpirationsNew.delete(username);
        return false;
      }

      // Reset creditsNew
      await UserNew.findByIdAndUpdate(username, {
        creditsNew: 0,
        purchasedAtNew: null,
        expiresAtNew: null,
      });

      // Log the reset (only when creditsNew > 0)
      await creditsResetLogRepository.create({
        username,
        creditsBefore,
        expiresAt: expiresAtNew || null,
        resetBy: triggeredBy,
        note: note ? `[creditsNew] ${note}` : '[creditsNew]',
      });

      // Remove from scheduled map
      scheduledExpirationsNew.delete(username);

      console.log(`[ExpirationScheduler] Reset ${username}: $${creditsBefore.toFixed(2)} creditsNew, triggered by ${triggeredBy}`);
      return true;
    } catch (error) {
      console.error(`[ExpirationScheduler] Error resetting ${username} creditsNew:`, error);
      return false;
    }
  }

  /**
   * Get count of scheduled expirations
   */
  getScheduledCount(): number {
    return scheduledExpirations.size;
  }

  /**
   * Get all scheduled usernames (for debugging)
   */
  getScheduledUsers(): string[] {
    return Array.from(scheduledExpirations.keys());
  }

  /**
   * Find all expired users with credits > 0 (for admin cleanup)
   */
  async findExpiredUsersWithCredits(): Promise<Array<{ username: string; credits: number; expiresAt: Date | null }>> {
    const now = new Date();
    const users = await UserNew.find({
      credits: { $gt: 0 },
      $or: [
        { expiresAt: null },
        { expiresAt: { $lt: now } },
      ],
    }).select('_id credits expiresAt').lean();

    return users.map(u => ({
      username: u._id,
      credits: u.credits,
      expiresAt: u.expiresAt || null,
    }));
  }

  /**
   * Bulk reset all expired users (admin action)
   */
  async bulkResetExpired(dryRun: boolean = false): Promise<{
    affected: number;
    totalCredits: number;
    users: Array<{ username: string; creditsBefore: number }>;
  }> {
    const expiredUsers = await this.findExpiredUsersWithCredits();

    if (dryRun) {
      return {
        affected: expiredUsers.length,
        totalCredits: expiredUsers.reduce((sum, u) => sum + u.credits, 0),
        users: expiredUsers.map(u => ({ username: u.username, creditsBefore: u.credits })),
      };
    }

    const results: Array<{ username: string; creditsBefore: number }> = [];
    let totalCredits = 0;

    for (const user of expiredUsers) {
      const success = await this.resetAndLog(user.username, 'admin');
      if (success) {
        results.push({ username: user.username, creditsBefore: user.credits });
        totalCredits += user.credits;
      }
    }

    return {
      affected: results.length,
      totalCredits,
      users: results,
    };
  }
}

export const expirationSchedulerService = ExpirationSchedulerService.getInstance();
