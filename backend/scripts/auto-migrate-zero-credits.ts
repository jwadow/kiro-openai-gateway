import mongoose from 'mongoose';

// MongoDB connection - use environment variable or default
const uri = process.env.MONGODB_URI || 'mongodb+srv://trantai306_db_user:FHBuXtedXaFLBr22@cluster0.aa02bn1.mongodb.net/fproxy?appName=Cluster0';

interface MigrationLog {
  userId: string;
  username: string;
  oldCredits: number;
  newCredits: number;
  migratedAt: Date;
  oldRate: number;
  newRate: number;
  autoMigrated: boolean;
}

async function autoMigrateZeroCreditUsers(dryRun: boolean = true) {
  try {
    await mongoose.connect(uri);

    // Define schema with _id as String (matching UserNew model)
    const userSchema = new mongoose.Schema({
      _id: { type: String, required: true },
      migration: Boolean,
      credits: Number,
      role: String,
      createdAt: Date,
    }, { strict: false });
    const UserNew = mongoose.model('UserNew', userSchema, 'usersNew');

    // Define MigrationLog schema
    const migrationLogSchema = new mongoose.Schema({
      userId: { type: String, required: true },
      username: { type: String, required: true },
      oldCredits: { type: Number, required: true },
      newCredits: { type: Number, required: true },
      migratedAt: { type: Date, default: Date.now },
      oldRate: { type: Number, required: true },
      newRate: { type: Number, required: true },
      autoMigrated: { type: Boolean, default: false },
    });
    const MigrationLog = mongoose.model('MigrationLog', migrationLogSchema, 'migration_logs');

    console.log('Connected to MongoDB');
    console.log(`Mode: ${dryRun ? 'DRY RUN (no changes will be made)' : 'APPLY (changes will be made)'}`);

    // Find users with migration: false and credits: 0
    const affectedUsers = await UserNew.find({
      migration: false,
      credits: 0,
    }).select('_id credits migration role createdAt').lean();

    console.log('\n=== AFFECTED USERS ===');
    console.log(`Found ${affectedUsers.length} users with migration=false and credits=0`);

    if (affectedUsers.length === 0) {
      console.log('No users need auto-migration. Exiting.');
      return;
    }

    // Show first 10 affected users
    console.log('\n=== SAMPLE AFFECTED USERS (first 10) ===');
    affectedUsers.slice(0, 10).forEach((user: any) => {
      console.log(`  - ${user._id} (credits=${user.credits}, migration=${user.migration}, role=${user.role})`);
    });

    if (affectedUsers.length > 10) {
      console.log(`  ... and ${affectedUsers.length - 10} more`);
    }

    if (dryRun) {
      console.log('\n=== DRY RUN COMPLETE ===');
      console.log('To apply changes, run with: npm run auto-migrate-zero-credits -- --apply');
    } else {
      // Apply changes
      console.log('\n=== APPLYING CHANGES ===');

      let successCount = 0;
      let errorCount = 0;

      for (const user of affectedUsers) {
        try {
          // Update user migration status - use native MongoDB update to avoid schema issues
          await mongoose.connection.collection('usersNew').updateOne(
            { _id: user._id },
            { $set: { migration: true } }
          );

          // Create migration log using native MongoDB to avoid schema issues
          await mongoose.connection.collection('migration_logs').insertOne({
            userId: user._id,
            username: user._id,
            oldCredits: 0,
            newCredits: 0,
            migratedAt: new Date(),
            oldRate: 1000,
            newRate: 2500,
            autoMigrated: true,
          } as MigrationLog);

          successCount++;
          if (successCount <= 10 || successCount % 50 === 0) {
            console.log(`  ✓ Auto-migrated: ${user._id}`);
          }
        } catch (error: any) {
          errorCount++;
          console.error(`  ✗ Failed to auto-migrate ${user._id}:`, error.message);
        }
      }

      console.log('\n=== RESULTS ===');
      console.log(`Successfully auto-migrated: ${successCount} users`);
      console.log(`Failed: ${errorCount} users`);

      // Verify results
      const remaining = await UserNew.countDocuments({
        migration: false,
        credits: 0,
      });

      console.log(`\nRemaining users with migration=false and credits=0: ${remaining}`);
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

console.log('=== Auto-Migrate Zero-Credit Users Script ===');
console.log('This script sets migration=true for users with credits=0');
console.log('These users have no credits to migrate, so they auto-migrate.\n');

autoMigrateZeroCreditUsers(dryRun)
  .then(() => {
    console.log('\nScript completed successfully.');
    process.exit(0);
  })
  .catch((error) => {
    console.error('\nScript failed:', error);
    process.exit(1);
  });
