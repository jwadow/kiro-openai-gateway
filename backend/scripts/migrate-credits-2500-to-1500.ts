/**
 * Credit Rate Migration Script (2500 VND/$1 → 1500 VND/$1)
 *
 * This script migrates existing user credits from the old rate (2500 VND/$1)
 * to the new rate (1500 VND/$1), preserving the VND value of credits.
 *
 * Formula: new_credits = old_credits × (2500 / 1500) = old_credits × 1.6667
 *
 * Example: $149 at 2500 VND/$1 = 372,500 VND → $248.33 at 1500 VND/$1 = 372,500 VND
 *
 * Usage:
 *   npm run migrate:2500-to-1500             # Dry-run mode (default, read-only)
 *   npm run migrate:2500-to-1500 -- --apply  # Apply mode (makes changes)
 *   npm run migrate:2500-to-1500 -- --apply --include-admins  # Include admin accounts
 *
 * Features:
 *   - Dry-run mode for safe testing
 *   - Idempotent (safe to re-run, skips already-migrated users)
 *   - Atomic per-user updates
 *   - Complete audit trail in migration_logs
 *   - Preserves refCredits (unchanged)
 */

import mongoose from 'mongoose';

// MongoDB connection - use environment variable or default
const uri = process.env.MONGODB_URI || 'mongodb+srv://trantai306_db_user:FHBuXtedXaFLBr22@cluster0.aa02bn1.mongodb.net/fproxy?appName=Cluster0';

// Migration constants
const OLD_RATE = 2500;  // Old rate: 2500 VND = $1 USD
const NEW_RATE = 1500;  // New rate: 1500 VND = $1 USD
const SCRIPT_VERSION = '2500-to-1500';

interface MigrationLog {
  userId: string;
  username: string;
  oldCredits: number;
  newCredits: number;
  migratedAt: Date;
  oldRate: number;
  newRate: number;
  scriptVersion: string;
  appliedBy: string;
  notes: string;
}

interface UserDocument {
  _id: string;
  credits: number;
  refCredits: number;
  role: string;
}

/**
 * Calculate new credit amount using rate conversion formula
 * Formula: new_credits = old_credits × (old_rate / new_rate)
 * Result is rounded to 2 decimal places (cents precision)
 */
function calculateNewCredits(oldCredits: number): number {
  const multiplier = OLD_RATE / NEW_RATE;
  const newCredits = oldCredits * multiplier;
  return Math.round(newCredits * 100) / 100; // Round to 2 decimal places
}

async function migrateCredits(dryRun: boolean = true, includeAdmins: boolean = false) {
  try {
    await mongoose.connect(uri);

    // Define schema with _id as String (matching UserNew model)
    const userSchema = new mongoose.Schema({
      _id: { type: String, required: true },
      credits: Number,
      refCredits: Number,
      role: String,
    }, { strict: false });
    const UserNew = mongoose.model('UserNew', userSchema, 'usersNew');

    console.log('Connected to MongoDB');
    console.log(`Mode: ${dryRun ? 'DRY RUN (no changes will be made)' : 'APPLY (changes will be made)'}`);
    console.log(`Admin accounts: ${includeAdmins ? 'INCLUDED' : 'EXCLUDED'}`);

    // Find users who need migration
    // 1. Users with credits > 0
    // 2. Users who don't have a migration log with scriptVersion: "2500-to-1500"

    // First, get all user IDs that have already been migrated
    const migratedUserIds = await mongoose.connection
      .collection('migration_logs')
      .find({ scriptVersion: SCRIPT_VERSION })
      .project({ userId: 1 })
      .toArray();

    const migratedSet = new Set(migratedUserIds.map((doc: any) => doc.userId));

    // Build query for users needing migration
    const query: any = {
      credits: { $gt: 0 },
      _id: { $nin: Array.from(migratedSet) }
    };

    // Exclude admins by default
    if (!includeAdmins) {
      query.role = { $ne: 'admin' };
    }

    const affectedUsers = await UserNew.find(query)
      .select('_id credits refCredits role')
      .sort({ _id: 1 })
      .lean() as UserDocument[];

    console.log('\n=== AFFECTED USERS ===');
    console.log(`Found ${affectedUsers.length} users needing migration`);

    if (affectedUsers.length === 0) {
      console.log('No users need migration. Exiting.');
      return;
    }

    // Calculate statistics
    let totalOldCredits = 0;
    let totalNewCredits = 0;

    affectedUsers.forEach(user => {
      totalOldCredits += user.credits;
      totalNewCredits += calculateNewCredits(user.credits);
    });

    // Show first 10 affected users
    console.log('\n=== SAMPLE AFFECTED USERS (first 10) ===');
    affectedUsers.slice(0, 10).forEach((user: UserDocument) => {
      const newCredits = calculateNewCredits(user.credits);
      console.log(`  - ${user._id}: $${user.credits.toFixed(2)} → $${newCredits.toFixed(2)} (role=${user.role}, refCredits=$${user.refCredits || 0})`);
    });

    if (affectedUsers.length > 10) {
      console.log(`  ... and ${affectedUsers.length - 10} more`);
    }

    // Display summary statistics
    console.log('\n=== MIGRATION PREVIEW ===');
    console.log(`Total users to migrate: ${affectedUsers.length}`);
    console.log(`Total credits before: $${totalOldCredits.toFixed(2)}`);
    console.log(`Total credits after: $${totalNewCredits.toFixed(2)}`);
    console.log(`Total increase: $${(totalNewCredits - totalOldCredits).toFixed(2)} (+${(((totalNewCredits - totalOldCredits) / totalOldCredits) * 100).toFixed(2)}%)`);

    if (dryRun) {
      console.log('\n=== DRY RUN COMPLETE ===');
      console.log('To apply changes, run with: npm run migrate:2500-to-1500 -- --apply');
    } else {
      // Apply changes
      console.log('\n=== APPLYING CHANGES ===');

      let successCount = 0;
      let skippedZeroCredits = 0;
      let failedCount = 0;

      for (const user of affectedUsers) {
        try {
          // Skip users with zero credits (shouldn't happen due to query, but safety check)
          if (user.credits === 0) {
            skippedZeroCredits++;
            console.log(`  ⊘ Skipped: ${user._id} (zero credits)`);
            continue;
          }

          const oldCredits = user.credits;
          const newCredits = calculateNewCredits(oldCredits);

          // Update user credits atomically
          const updateResult = await mongoose.connection.collection('usersNew').updateOne(
            { _id: user._id },
            { $set: { credits: newCredits } }
          );

          if (updateResult.modifiedCount === 0) {
            throw new Error('Update did not modify any document');
          }

          // Create migration log
          await mongoose.connection.collection('migration_logs').insertOne({
            userId: user._id,
            username: user._id,
            oldCredits: oldCredits,
            newCredits: newCredits,
            migratedAt: new Date(),
            oldRate: OLD_RATE,
            newRate: NEW_RATE,
            scriptVersion: SCRIPT_VERSION,
            appliedBy: 'admin',
            notes: `Automatic rate migration from ${OLD_RATE} to ${NEW_RATE} VND/$`
          } as MigrationLog);

          successCount++;
          if (successCount <= 10 || successCount % 50 === 0) {
            console.log(`  ✓ Migrated: ${user._id} ($${oldCredits.toFixed(2)} → $${newCredits.toFixed(2)})`);
          }
        } catch (error: any) {
          failedCount++;
          console.error(`  ✗ Failed: ${user._id} - ${error.message}`);
        }
      }

      console.log('\n=== MIGRATION SUMMARY ===');
      console.log(`Total users processed: ${affectedUsers.length}`);
      console.log(`Successfully migrated: ${successCount}`);
      if (skippedZeroCredits > 0) {
        console.log(`Skipped (zero credits): ${skippedZeroCredits}`);
      }
      if (failedCount > 0) {
        console.log(`Failed: ${failedCount}`);
      }

      // Calculate actual totals
      const actualOldTotal = affectedUsers.slice(0, successCount).reduce((sum, u) => sum + u.credits, 0);
      const actualNewTotal = affectedUsers.slice(0, successCount).reduce((sum, u) => sum + calculateNewCredits(u.credits), 0);

      console.log(`\nTotal credits before: $${actualOldTotal.toFixed(2)}`);
      console.log(`Total credits after: $${actualNewTotal.toFixed(2)}`);
      console.log(`Total increase: $${(actualNewTotal - actualOldTotal).toFixed(2)} (+${(((actualNewTotal - actualOldTotal) / actualOldTotal) * 100).toFixed(2)}%)`);

      // Verify remaining unmigrated users
      const stillMigrated = await mongoose.connection
        .collection('migration_logs')
        .find({ scriptVersion: SCRIPT_VERSION })
        .count();

      const remainingQuery: any = {
        credits: { $gt: 0 }
      };
      if (!includeAdmins) {
        remainingQuery.role = { $ne: 'admin' };
      }

      const remaining = await UserNew.countDocuments(remainingQuery) - stillMigrated;

      console.log(`\nRemaining unmigrated users: ${remaining}`);
    }

  } catch (error: any) {
    console.error('Error:', error);
    throw error;
  } finally {
    await mongoose.disconnect();
    console.log('\nDisconnected from MongoDB');
  }
}

// Parse command line arguments
const args = process.argv.slice(2);
const dryRun = !args.includes('--apply');
const includeAdmins = args.includes('--include-admins');

console.log('=== Credit Rate Migration Script (2500 → 1500) ===');
console.log('This script converts user credits to preserve VND value.');
console.log(`Formula: new_credits = old_credits × (${OLD_RATE} / ${NEW_RATE}) = old_credits × ${(OLD_RATE / NEW_RATE).toFixed(4)}\n`);

migrateCredits(dryRun, includeAdmins)
  .then(() => {
    console.log('\nScript completed successfully.');
    process.exit(0);
  })
  .catch((error) => {
    console.error('\nScript failed:', error);
    process.exit(1);
  });
