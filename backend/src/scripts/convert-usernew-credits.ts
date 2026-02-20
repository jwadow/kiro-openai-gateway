import 'dotenv/config';
import mongoose from 'mongoose';
import { UserNew } from '../models/user-new.model.js';

// Conversion constants
const VND_PER_OLD_CREDIT = 144; // 1,250 credits = 180,000đ → 1 credit = 144đ
const VND_PER_NEW_DOLLAR = 1000; // OLD rate: $1 = 1,000 VND (now updated to 2,500 VND)
const BALANCE_THRESHOLD = 50; // $50 threshold for expiration
const ONE_WEEK_MS = 7 * 24 * 60 * 60 * 1000;
const TWO_WEEKS_MS = 14 * 24 * 60 * 60 * 1000;

/**
 * Round up to nearest 0.5
 * Examples: 79.2 → 79.5, 79.6 → 80, 79.0 → 79.0
 */
function roundUpToHalf(value: number): number {
  return Math.ceil(value * 2) / 2;
}

/**
 * Convert old credits to new dollar balance
 * Formula: ((credits + refCredits) * 144) / 1000
 */
function convertCredits(credits: number, refCredits: number): number {
  const totalOldCredits = credits + refCredits;
  const vndValue = totalOldCredits * VND_PER_OLD_CREDIT;
  const newBalance = vndValue / VND_PER_NEW_DOLLAR;
  return roundUpToHalf(newBalance);
}

async function convertUsersNewCredits() {
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
    const now = new Date();
    const oneWeekLater = new Date(now.getTime() + ONE_WEEK_MS);
    const twoWeeksLater = new Date(now.getTime() + TWO_WEEKS_MS);

    // Fetch all users with credits or refCredits > 0
    const users = await UserNew.find({
      $or: [
        { credits: { $gt: 0 } },
        { refCredits: { $gt: 0 } }
      ]
    }).lean();

    console.log(`\n📊 Found ${users.length} users with credits to convert`);

    if (users.length === 0) {
      console.log('ℹ️  No users to convert');
      await mongoose.disconnect();
      return;
    }

    let converted = 0;
    let failed = 0;
    const conversions: Array<{
      username: string;
      oldCredits: number;
      oldRefCredits: number;
      newCredits: number;
      expiresIn: string;
    }> = [];

    for (const user of users) {
      try {
        const oldCredits = user.credits || 0;
        const oldRefCredits = user.refCredits || 0;
        const newCredits = convertCredits(oldCredits, oldRefCredits);

        // All users get 2 weeks expiration
        const expiresAt = twoWeeksLater;
        const expiresIn = '2 weeks';

        // Update user
        await UserNew.updateOne(
          { _id: user._id },
          {
            $set: {
              credits: newCredits,
              refCredits: 0,
              purchasedAt: now,
              expiresAt: expiresAt,
            }
          }
        );

        conversions.push({
          username: user._id,
          oldCredits,
          oldRefCredits,
          newCredits,
          expiresIn,
        });

        converted++;
      } catch (err) {
        console.error(`❌ Failed to convert ${user._id}:`, err);
        failed++;
      }
    }

    // Log conversion details
    console.log('\n📋 Conversion Details:');
    console.log('─'.repeat(80));
    console.log(
      'Username'.padEnd(25) +
      'Old Credits'.padEnd(15) +
      'Old RefCredits'.padEnd(15) +
      'New Balance'.padEnd(15) +
      'Expires'
    );
    console.log('─'.repeat(80));

    for (const c of conversions) {
      console.log(
        c.username.padEnd(25) +
        c.oldCredits.toString().padEnd(15) +
        c.oldRefCredits.toString().padEnd(15) +
        `$${c.newCredits}`.padEnd(15) +
        c.expiresIn
      );
    }

    console.log('─'.repeat(80));
    console.log(`\n📊 Conversion Summary:`);
    console.log(`   Total users processed: ${users.length}`);
    console.log(`   Successfully converted: ${converted}`);
    console.log(`   Failed: ${failed}`);
    console.log(`   Expiration: All users get 2 weeks`);

    if (converted === users.length) {
      console.log('\n✅ All credits converted successfully!');
    } else {
      console.log('\n⚠️  Some conversions failed. Check errors above.');
    }

  } catch (err) {
    console.error('❌ Conversion failed:', err);
  } finally {
    await mongoose.disconnect();
    console.log('\n🔌 Disconnected from MongoDB');
  }
}

convertUsersNewCredits().catch(err => {
  console.error('❌ Script failed:', err);
  process.exit(1);
});
