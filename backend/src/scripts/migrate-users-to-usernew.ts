import 'dotenv/config';
import mongoose from 'mongoose';
import { User } from '../models/user.model.js';
import { UserNew } from '../models/user-new.model.js';

async function migrateUsersToUsersNew() {
  const mongoUri = process.env.MONGODB_URI;
  if (!mongoUri) {
    console.error('❌ MONGODB_URI not set');
    process.exit(1);
  }

  const dbName = process.env.MONGODB_DB_NAME || 'fproxy';
  console.log(`🔌 Connecting to MongoDB (database: ${dbName})...`);
  await mongoose.connect(mongoUri, { dbName });
  console.log('✅ Connected to MongoDB');

  try {
    // Count existing documents
    const sourceCount = await User.countDocuments();
    console.log(`📊 Source collection (users): ${sourceCount} documents`);

    const existingTargetCount = await UserNew.countDocuments();
    console.log(`📊 Target collection (usersNew): ${existingTargetCount} documents`);

    if (existingTargetCount > 0) {
      console.log('⚠️  Target collection is not empty. Do you want to continue?');
      console.log('   This will add documents without clearing existing ones.');
      console.log('   To clear the target collection first, run:');
      console.log('   db.usersNew.drop()');
    }

    // Fetch all users from source collection
    console.log('\n📥 Fetching all users from source collection...');
    const users = await User.find({}).lean();
    console.log(`✅ Fetched ${users.length} users`);

    if (users.length === 0) {
      console.log('ℹ️  No users to migrate');
      await mongoose.disconnect();
      return;
    }

    // Insert into target collection
    console.log('\n📤 Inserting users into usersNew collection...');

    let inserted = 0;
    let failed = 0;
    const failedUsers: string[] = [];

    // Insert in batches of 100 for better performance and error handling
    const batchSize = 100;
    for (let i = 0; i < users.length; i += batchSize) {
      const batch = users.slice(i, i + batchSize);

      try {
        await UserNew.insertMany(batch, { ordered: false });
        inserted += batch.length;
        console.log(`   ✅ Inserted batch ${Math.floor(i / batchSize) + 1}: ${batch.length} documents`);
      } catch (err: any) {
        // Handle duplicate key errors - some may have succeeded
        if (err.code === 11000) {
          const insertedCount = err.insertedDocs?.length || 0;
          inserted += insertedCount;
          failed += batch.length - insertedCount;

          // Log failed user IDs
          for (const user of batch) {
            const exists = await UserNew.exists({ _id: user._id });
            if (!exists) {
              failedUsers.push(user._id);
            }
          }

          console.log(`   ⚠️  Batch ${Math.floor(i / batchSize) + 1}: ${insertedCount} inserted, ${batch.length - insertedCount} duplicates/failed`);
        } else {
          failed += batch.length;
          console.error(`   ❌ Batch ${Math.floor(i / batchSize) + 1} failed:`, err.message);
          for (const user of batch) {
            failedUsers.push(user._id);
          }
        }
      }
    }

    // Verify migration
    const targetCount = await UserNew.countDocuments();

    console.log('\n📊 Migration Summary:');
    console.log(`   Source documents: ${sourceCount}`);
    console.log(`   Successfully inserted: ${inserted}`);
    console.log(`   Failed: ${failed}`);
    console.log(`   Target documents (total): ${targetCount}`);

    if (failedUsers.length > 0 && failedUsers.length <= 20) {
      console.log('\n❌ Failed user IDs:');
      for (const userId of failedUsers) {
        console.log(`   - ${userId}`);
      }
    } else if (failedUsers.length > 20) {
      console.log(`\n❌ ${failedUsers.length} users failed. First 20:`);
      for (const userId of failedUsers.slice(0, 20)) {
        console.log(`   - ${userId}`);
      }
    }

    if (targetCount === sourceCount) {
      console.log('\n✅ Migration completed successfully! All documents migrated.');
    } else if (targetCount > 0) {
      console.log('\n⚠️  Migration completed with some issues.');
    } else {
      console.log('\n❌ Migration failed. No documents were inserted.');
    }

  } catch (err) {
    console.error('❌ Migration failed:', err);
  } finally {
    await mongoose.disconnect();
    console.log('\n🔌 Disconnected from MongoDB');
  }
}

migrateUsersToUsersNew().catch(err => {
  console.error('❌ Script failed:', err);
  process.exit(1);
});
