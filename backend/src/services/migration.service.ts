import { userNewRepository } from '../repositories/user-new.repository.js';

export class MigrationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'MigrationError';
  }
}

export interface MigrationResult {
  success: boolean;
  oldCredits: number;
  newCredits: number;
  message: string;
}

export class MigrationService {
  async processMigration(userId: string): Promise<MigrationResult> {
    // Validate user exists
    const user = await userNewRepository.findById(userId);
    if (!user) {
      throw new MigrationError('User not found');
    }

    // Check if already migrated
    if (user.migration) {
      throw new MigrationError('User has already migrated');
    }

    // Perform migration (manual, not auto-migrated)
    const result = await userNewRepository.setMigrated(userId, false);

    if (!result) {
      throw new MigrationError('Migration failed - user may already be migrated');
    }

    return {
      success: true,
      oldCredits: result.oldCredits,
      newCredits: result.newCredits,
      message: `Successfully migrated from ${result.oldCredits.toFixed(2)} to ${result.newCredits.toFixed(2)} credits`,
    };
  }

  async getMigrationStatus(userId: string): Promise<boolean> {
    return userNewRepository.getMigrationStatus(userId);
  }

  /**
   * Auto-migrate users with zero credits.
   * Returns true if auto-migration was performed, false otherwise.
   */
  async autoMigrateIfZeroCredits(userId: string): Promise<boolean> {
    const user = await userNewRepository.findById(userId);
    if (!user) {
      return false;
    }

    // Skip if already migrated
    if (user.migration) {
      return false;
    }

    // Only auto-migrate if credits is exactly 0
    if (user.credits !== 0) {
      return false;
    }

    // Perform auto-migration
    const result = await userNewRepository.setMigrated(userId, true);
    return result !== null;
  }
}

export const migrationService = new MigrationService();
