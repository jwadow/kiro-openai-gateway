/**
 * Script: Extend expiresAtNew due to server maintenance
 * 
 * Maintenance window: 4:35 AM - 10:50 AM (6 hours 15 minutes = 375 minutes)
 * This script adds 375 minutes to expiresAtNew for all users who:
 * - Have a valid expiresAtNew (not null)
 * - Their expiresAtNew has not yet expired (>= now)
 * 
 * Usage: tsx src/scripts/extend-expires-maintenance.ts [--dry-run]
 */
import mongoose from 'mongoose';
import * as dotenv from 'dotenv';

dotenv.config();

const MONGODB_URI = process.env.MONGODB_URI || '';
const MONGODB_DB_NAME = process.env.MONGODB_DB_NAME || 'trollllm';

// Maintenance duration: 4:35 AM to 10:50 AM = 6h 15m = 375 minutes
const MAINTENANCE_MINUTES = 375;

async function extendExpiresAtNew(dryRun: boolean = false) {
  try {
    await mongoose.connect(MONGODB_URI, { dbName: MONGODB_DB_NAME });
    console.log('✅ Connected to MongoDB');
    console.log(`📋 Database: ${MONGODB_DB_NAME}`);
    console.log(`⏱️  Maintenance duration: ${MAINTENANCE_MINUTES} minutes (6h 15m)`);
    console.log(`🔧 Mode: ${dryRun ? 'DRY RUN (no changes)' : 'LIVE (will update)'}\n`);

    const db = mongoose.connection.db;
    if (!db) {
      throw new Error('Database connection not established');
    }

    const now = new Date();
    console.log(`📅 Current time: ${now.toISOString()}\n`);

    // Find all users with valid, non-expired expiresAtNew
    const usersToUpdate = await db.collection('usersNew').find({
      expiresAtNew: { $ne: null, $gte: now }
    }).toArray();

    console.log(`📊 Found ${usersToUpdate.length} users with valid expiresAtNew\n`);

    if (usersToUpdate.length === 0) {
      console.log('ℹ️  No users need extension.');
      return;
    }

    // Preview changes
    console.log('========== PREVIEW ==========');
    for (const user of usersToUpdate) {
      const oldExpires = new Date(user.expiresAtNew);
      const newExpires = new Date(oldExpires.getTime() + MAINTENANCE_MINUTES * 60 * 1000);
      console.log(`👤 ${user._id}`);
      console.log(`   Old: ${oldExpires.toISOString()}`);
      console.log(`   New: ${newExpires.toISOString()}`);
      console.log(`   Added: +${MAINTENANCE_MINUTES} minutes\n`);
    }

    if (dryRun) {
      console.log('========== DRY RUN COMPLETE ==========');
      console.log('No changes were made. Remove --dry-run flag to apply changes.');
      return;
    }

    // Apply changes
    console.log('========== APPLYING CHANGES ==========');
    
    const result = await db.collection('usersNew').updateMany(
      {
        expiresAtNew: { $ne: null, $gte: now }
      },
      [
        {
          $set: {
            expiresAtNew: {
              $dateAdd: {
                startDate: '$expiresAtNew',
                unit: 'minute',
                amount: MAINTENANCE_MINUTES
              }
            }
          }
        }
      ]
    );

    console.log(`✅ Updated ${result.modifiedCount} users`);
    console.log(`   Matched: ${result.matchedCount}`);
    console.log(`   Modified: ${result.modifiedCount}`);

    // Verify changes
    console.log('\n========== VERIFICATION ==========');
    for (const user of usersToUpdate.slice(0, 5)) {
      const updated = await db.collection('usersNew').findOne({ _id: user._id });
      if (updated) {
        console.log(`👤 ${user._id}: ${new Date(updated.expiresAtNew).toISOString()}`);
      }
    }
    if (usersToUpdate.length > 5) {
      console.log(`   ... and ${usersToUpdate.length - 5} more users`);
    }

    console.log('\n✅ Script completed successfully!');

  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  } finally {
    await mongoose.disconnect();
    console.log('\n🔌 Disconnected from MongoDB');
  }
}

// Parse command line arguments
const args = process.argv.slice(2);
const dryRun = args.includes('--dry-run');

console.log('='.repeat(50));
console.log('🔧 MAINTENANCE COMPENSATION SCRIPT');
console.log('   Extend expiresAtNew by 6h 15m (375 minutes)');
console.log('   Maintenance: 4:35 AM - 10:50 AM');
console.log('='.repeat(50) + '\n');

extendExpiresAtNew(dryRun);
