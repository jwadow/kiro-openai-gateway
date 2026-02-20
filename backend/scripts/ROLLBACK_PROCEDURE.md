# Credit Migration Rollback Procedure

This document describes how to verify migration success and rollback if needed.

## Verification Queries

### Check Migration Logs

```javascript
// Connect to MongoDB
use fproxy

// Count total migrations for this version
db.migration_logs.countDocuments({ scriptVersion: "2500-to-1500" })

// View sample migration logs
db.migration_logs.find({ scriptVersion: "2500-to-1500" }).limit(10).pretty()

// Check for any failures (if you logged them separately)
db.migration_logs.find({
  scriptVersion: "2500-to-1500",
  notes: /failed/i
}).pretty()

// Verify migration statistics
db.migration_logs.aggregate([
  { $match: { scriptVersion: "2500-to-1500" } },
  { $group: {
    _id: null,
    totalUsers: { $sum: 1 },
    totalOldCredits: { $sum: "$oldCredits" },
    totalNewCredits: { $sum: "$newCredits" },
    avgMultiplier: { $avg: { $divide: ["$newCredits", "$oldCredits"] } }
  }}
])
```

### Check User Credits

```javascript
// Find a specific user to verify migration
db.usersNew.findOne({ _id: "username" }, { credits: 1, refCredits: 1 })

// Spot-check 10 random users who were migrated
const migratedUserIds = db.migration_logs
  .find({ scriptVersion: "2500-to-1500" })
  .limit(10)
  .map(log => log.userId)

db.usersNew.find({ _id: { $in: migratedUserIds } }, { _id: 1, credits: 1, refCredits: 1 }).pretty()
```

### Check for Unmigrated Users

```javascript
// Get list of migrated user IDs
const migrated = db.migration_logs
  .find({ scriptVersion: "2500-to-1500" })
  .map(log => log.userId)

// Find users with credits > 0 who aren't migrated
db.usersNew.countDocuments({
  credits: { $gt: 0 },
  role: { $ne: 'admin' },
  _id: { $nin: migrated }
})

// Show sample unmigrated users
db.usersNew.find({
  credits: { $gt: 0 },
  role: { $ne: 'admin' },
  _id: { $nin: migrated }
}).limit(10).pretty()
```

## Manual Rollback Procedure

If the migration needs to be rolled back, follow these steps:

### Step 1: Create Backup (CRITICAL)

Before rollback, ensure you have a backup of the current state:

```bash
# Using mongodump
mongodump --uri="mongodb+srv://..." --db=fproxy --collection=usersNew --out=/backup/post-migration

# Or using MongoDB Atlas backup feature
# Navigate to Atlas > Cluster > Backup > Download Snapshot
```

### Step 2: Rollback Formula

The reverse formula to undo the migration:

```
old_credits = new_credits ÷ (2500 / 1500)
old_credits = new_credits ÷ 1.6667
old_credits = new_credits × 0.6
```

### Step 3: Create Rollback Script

Create `backend/scripts/rollback-credits-2500-to-1500.ts`:

```typescript
import mongoose from 'mongoose';

const uri = process.env.MONGODB_URI || 'mongodb+srv://...';

async function rollbackMigration() {
  try {
    await mongoose.connect(uri);
    console.log('Connected to MongoDB');

    // Get all users who were migrated
    const migratedLogs = await mongoose.connection
      .collection('migration_logs')
      .find({ scriptVersion: '2500-to-1500' })
      .toArray();

    console.log(`Found ${migratedLogs.length} users to rollback`);

    let successCount = 0;
    let failedCount = 0;

    for (const log of migratedLogs) {
      try {
        // Restore original credits
        const result = await mongoose.connection
          .collection('usersNew')
          .updateOne(
            { _id: log.userId },
            { $set: { credits: log.oldCredits } }
          );

        if (result.modifiedCount > 0) {
          successCount++;
          console.log(`✓ Rolled back: ${log.userId} (${log.newCredits} → ${log.oldCredits})`);
        }
      } catch (error) {
        failedCount++;
        console.error(`✗ Failed to rollback: ${log.userId}`, error);
      }
    }

    console.log(`\nRollback complete: ${successCount} success, ${failedCount} failed`);

    // Optionally remove migration logs
    // await mongoose.connection.collection('migration_logs').deleteMany({ scriptVersion: '2500-to-1500' });

  } catch (error) {
    console.error('Rollback failed:', error);
    throw error;
  } finally {
    await mongoose.disconnect();
  }
}

rollbackMigration()
  .then(() => process.exit(0))
  .catch(() => process.exit(1));
```

### Step 4: Execute Rollback

```bash
# Test on development first
MONGODB_URI="mongodb://dev..." tsx backend/scripts/rollback-credits-2500-to-1500.ts

# Then on production (with extreme caution)
MONGODB_URI="mongodb+srv://prod..." tsx backend/scripts/rollback-credits-2500-to-1500.ts
```

### Step 5: Verify Rollback

After rollback, verify using the verification queries above:

```javascript
// Check if users are back to original credits
db.migration_logs.aggregate([
  { $match: { scriptVersion: "2500-to-1500" } },
  { $lookup: {
    from: "usersNew",
    localField: "userId",
    foreignField: "_id",
    as: "currentUser"
  }},
  { $project: {
    userId: 1,
    oldCredits: 1,
    newCredits: 1,
    currentCredits: { $arrayElemAt: ["$currentUser.credits", 0] },
    rolledBack: { $eq: [{ $arrayElemAt: ["$currentUser.credits", 0] }, "$oldCredits"] }
  }}
]).limit(10).pretty()
```

## Prevention for Future

To prevent the need for rollback in future migrations:

1. Always run dry-run mode first on production
2. Test thoroughly on development/staging
3. Migrate a small batch first (10-20 users) and verify
4. Have database backup before applying
5. Monitor user reports for 24-48 hours after migration
6. Keep migration logs indefinitely for audit trail

## Contact

If issues arise during verification or rollback:
- Check migration logs in MongoDB
- Review script execution logs
- Contact system administrator
- Restore from pre-migration backup if necessary
