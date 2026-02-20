const mongoose = require('mongoose');

// MongoDB connection
const uri = process.env.MONGODB_URI || 'mongodb+srv://trantai306_db_user:FHBuXtedXaFLBr22@cluster0.aa02bn1.mongodb.net/fproxy?appName=Cluster0';

// Rate change announcement date
const RATE_CHANGE_DATE = new Date('2026-01-06T00:00:00.000Z');

async function fixNewUserMigrationDefault(dryRun = true) {
  try {
    await mongoose.connect(uri);

    // Define schema with strict: false to access all fields
    const userSchema = new mongoose.Schema({}, { strict: false });
    const UserNew = mongoose.model('UserNew', userSchema, 'usersNew');

    console.log('Connected to MongoDB');
    console.log('Mode:', dryRun ? 'DRY RUN (no changes will be made)' : 'APPLY (changes will be made)');

    // Check current stats
    const totalUsers = await UserNew.countDocuments();
    const migrationFalse = await UserNew.countDocuments({ migration: false });
    const migrationTrue = await UserNew.countDocuments({ migration: true });

    // Find users created after rate change with migration: false
    const affectedUsers = await UserNew.find({
      migration: false,
      createdAt: { $gte: RATE_CHANGE_DATE }
    }).select('_id createdAt migration role').lean();

    console.log('\n=== CURRENT DATABASE STATE ===');
    console.log('Total users:', totalUsers);
    console.log('Migration = false:', migrationFalse);
    console.log('Migration = true:', migrationTrue);

    console.log('\n=== AFFECTED USERS (created after 2026-01-06 with migration: false) ===');
    console.log('Found:', affectedUsers.length, 'users');

    if (affectedUsers.length > 0) {
      console.log('\nUsers to be updated:');
      affectedUsers.forEach((user, index) => {
        console.log(`  ${index + 1}. ${user._id} (created: ${user.createdAt.toISOString()}, role: ${user.role})`);
      });

      if (!dryRun) {
        console.log('\n=== APPLYING CHANGES ===');
        const result = await UserNew.updateMany(
          {
            migration: false,
            createdAt: { $gte: RATE_CHANGE_DATE }
          },
          { $set: { migration: true } }
        );

        console.log('Matched:', result.matchedCount);
        console.log('Modified:', result.modifiedCount);

        // Verify after update
        const afterFalse = await UserNew.countDocuments({ migration: false });
        const afterTrue = await UserNew.countDocuments({ migration: true });

        console.log('\n=== AFTER UPDATE ===');
        console.log('Migration = false:', afterFalse);
        console.log('Migration = true:', afterTrue);
      } else {
        console.log('\n=== DRY RUN COMPLETE ===');
        console.log('No changes were made.');
        console.log('To apply changes, run: node backend/scripts/fix-new-user-migration-default.js apply');
      }
    } else {
      console.log('\n✓ No users need migration. All new users already have migration: true');
    }

    // Show users created before rate change with migration: false (these should remain false)
    const existingNonMigrated = await UserNew.find({
      migration: false,
      createdAt: { $lt: RATE_CHANGE_DATE }
    }).select('_id createdAt migration role').limit(10).lean();

    console.log('\n=== EXISTING NON-MIGRATED USERS (created before 2026-01-06) ===');
    console.log('These users should remain with migration: false (they need manual migration)');
    console.log('Showing first 10:');
    existingNonMigrated.forEach((user, index) => {
      console.log(`  ${index + 1}. ${user._id} (created: ${user.createdAt.toISOString()})`);
    });
    const totalExistingNonMigrated = await UserNew.countDocuments({
      migration: false,
      createdAt: { $lt: RATE_CHANGE_DATE }
    });
    console.log(`Total existing non-migrated users: ${totalExistingNonMigrated}`);

  } catch (error) {
    console.error('Error:', error);
    process.exit(1);
  } finally {
    await mongoose.disconnect();
    console.log('\nDisconnected from MongoDB');
  }
}

// Check command line arguments
const args = process.argv.slice(2);
const dryRun = args[0] !== 'apply';

console.log('=============================================================');
console.log('Fix New User Migration Default');
console.log('=============================================================');
console.log('This script fixes new users (created after 2026-01-06)');
console.log('who incorrectly have migration: false');
console.log('=============================================================\n');

fixNewUserMigrationDefault(dryRun)
  .then(() => {
    console.log('\n✓ Script completed successfully');
    process.exit(0);
  })
  .catch((error) => {
    console.error('\n✗ Script failed:', error);
    process.exit(1);
  });
