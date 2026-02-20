import 'dotenv/config';
import mongoose from 'mongoose';
import { User, generateReferralCode } from '../models/user.model.js';

async function generateReferralCodesForExistingUsers() {
  const mongoUri = process.env.MONGODB_URI;
  if (!mongoUri) {
    console.error('❌ MONGODB_URI not set');
    process.exit(1);
  }

  const dbName = process.env.MONGODB_DB_NAME || 'fproxy';
  console.log(`🔌 Connecting to MongoDB (database: ${dbName})...`);
  await mongoose.connect(mongoUri, { dbName });
  console.log('✅ Connected to MongoDB');

  // First, let's see what we have
  const allUsers = await User.find({}).select('_id referralCode').lean();
  console.log(`📊 Total users in database: ${allUsers.length}`);
  
  // Log some sample referral codes
  const sampleUsers = allUsers.slice(0, 5);
  console.log('📋 Sample users:');
  for (const u of sampleUsers) {
    console.log(`   ${u._id}: referralCode = "${u.referralCode}" (type: ${typeof u.referralCode})`);
  }

  // Find users without valid referral code
  const usersWithoutCode = await User.find({
    $or: [
      { referralCode: { $exists: false } },
      { referralCode: null },
      { referralCode: '' },
      { referralCode: 'undefined' },
      { referralCode: { $type: 'undefined' } }
    ]
  }).lean();

  console.log(`\n📋 Found ${usersWithoutCode.length} users without valid referral code`);

  let updated = 0;
  let failed = 0;

  for (const user of usersWithoutCode) {
    try {
      // Generate unique referral code
      let referralCode = generateReferralCode();
      let attempts = 0;
      while (await User.exists({ referralCode }) && attempts < 10) {
        referralCode = generateReferralCode();
        attempts++;
      }

      // Update user
      await User.updateOne(
        { _id: user._id },
        { 
          $set: { 
            referralCode,
            refCredits: (user as any).refCredits ?? 0,
            referralBonusAwarded: (user as any).referralBonusAwarded ?? false
          } 
        }
      );

      console.log(`✅ Generated code for ${user._id}: ${referralCode}`);
      updated++;
    } catch (err) {
      console.error(`❌ Failed to update ${user._id}:`, err);
      failed++;
    }
  }

  console.log('\n📊 Summary:');
  console.log(`   Updated: ${updated}`);
  console.log(`   Failed: ${failed}`);
  console.log(`   Total: ${usersWithoutCode.length}`);

  await mongoose.disconnect();
  console.log('\n✅ Done!');
}

generateReferralCodesForExistingUsers().catch(err => {
  console.error('❌ Script failed:', err);
  process.exit(1);
});
