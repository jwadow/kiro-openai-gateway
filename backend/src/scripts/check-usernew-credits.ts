import 'dotenv/config';
import mongoose from 'mongoose';
import { UserNew } from '../models/user-new.model.js';

async function checkUsersNewCredits() {
  const mongoUri = process.env.MONGODB_URI;
  if (!mongoUri) {
    console.error('❌ MONGODB_URI not set');
    process.exit(1);
  }

  const dbName = process.env.MONGODB_DB_NAME || 'fproxy';
  console.log(`🔌 Connecting to MongoDB (database: ${dbName})...`);
  await mongoose.connect(mongoUri, { dbName });
  console.log('✅ Connected to MongoDB\n');

  try {
    // Get all users with credits
    const allUsers = await UserNew.find({
      $or: [{ credits: { $gt: 0 } }, { refCredits: { $gt: 0 } }]
    })
      .select('_id credits refCredits expiresAt purchasedAt')
      .sort({ credits: -1 })
      .lean();

    console.log(`📊 Total users with credits/refCredits: ${allUsers.length}\n`);

    // Users with >= 50 credits
    const usersOver50 = allUsers.filter(u => u.credits >= 50);
    // Users with < 50 credits
    const usersUnder50 = allUsers.filter(u => u.credits < 50 && u.credits > 0);

    console.log('═'.repeat(90));
    console.log('USERS WITH CREDITS >= $50 (should have 2 weeks expiration)');
    console.log('═'.repeat(90));
    console.log(
      'Username'.padEnd(30) +
      'Credits'.padEnd(12) +
      'RefCredits'.padEnd(12) +
      'ExpiresAt'.padEnd(25) +
      'Days'
    );
    console.log('─'.repeat(90));

    for (const u of usersOver50) {
      const expiresAt = u.expiresAt ? new Date(u.expiresAt).toISOString().slice(0, 19) : 'N/A';
      const purchasedAt = u.purchasedAt ? new Date(u.purchasedAt) : null;

      let days = 'N/A';
      if (u.expiresAt && purchasedAt) {
        const diffMs = new Date(u.expiresAt).getTime() - purchasedAt.getTime();
        days = (diffMs / (1000 * 60 * 60 * 24)).toFixed(1);
      }

      console.log(
        String(u._id).padEnd(30) +
        String(u.credits).padEnd(12) +
        String(u.refCredits || 0).padEnd(12) +
        expiresAt.padEnd(25) +
        days
      );
    }
    console.log(`\nTotal >= $50: ${usersOver50.length} users`);

    console.log('\n' + '═'.repeat(90));
    console.log('USERS WITH CREDITS < $50 (should have 1 week expiration)');
    console.log('═'.repeat(90));
    console.log(
      'Username'.padEnd(30) +
      'Credits'.padEnd(12) +
      'RefCredits'.padEnd(12) +
      'ExpiresAt'.padEnd(25) +
      'Days'
    );
    console.log('─'.repeat(90));

    for (const u of usersUnder50) {
      const expiresAt = u.expiresAt ? new Date(u.expiresAt).toISOString().slice(0, 19) : 'N/A';
      const purchasedAt = u.purchasedAt ? new Date(u.purchasedAt) : null;

      let days = 'N/A';
      if (u.expiresAt && purchasedAt) {
        const diffMs = new Date(u.expiresAt).getTime() - purchasedAt.getTime();
        days = (diffMs / (1000 * 60 * 60 * 24)).toFixed(1);
      }

      console.log(
        String(u._id).padEnd(30) +
        String(u.credits).padEnd(12) +
        String(u.refCredits || 0).padEnd(12) +
        expiresAt.padEnd(25) +
        days
      );
    }
    console.log(`\nTotal < $50: ${usersUnder50.length} users`);

    console.log('\n' + '═'.repeat(90));
    console.log('SUMMARY');
    console.log('═'.repeat(90));
    console.log(`Total users with balance: ${allUsers.length}`);
    console.log(`  - >= $50 (2 weeks): ${usersOver50.length}`);
    console.log(`  - < $50 (1 week): ${usersUnder50.length}`);

  } catch (err) {
    console.error('❌ Check failed:', err);
  } finally {
    await mongoose.disconnect();
    console.log('\n🔌 Disconnected from MongoDB');
  }
}

checkUsersNewCredits().catch(err => {
  console.error('❌ Script failed:', err);
  process.exit(1);
});
