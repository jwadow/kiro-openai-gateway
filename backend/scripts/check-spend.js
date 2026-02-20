const { MongoClient } = require('mongodb');
require('dotenv').config();

const KEY_BUDGET = 10; // Mỗi key có budget $10

async function checkSpend() {
  const uri = process.env.MONGODB_URI;
  if (!uri) {
    console.error('❌ MONGODB_URI environment variable is not set');
    process.exit(1);
  }

  const dbName = process.env.MONGODB_DB_NAME || 'fproxy';

  const client = new MongoClient(uri);

  try {
    await client.connect();
    console.log('✅ Connected to MongoDB');

    const db = client.db(dbName);
    const collection = db.collection('openhands_keys');

    // Đếm tổng số keys
    const totalKeys = await collection.countDocuments();

    // Tính tổng totalSpend
    const result = await collection.aggregate([
      {
        $group: {
          _id: null,
          totalSpend: { $sum: '$totalSpend' }
        }
      }
    ]).toArray();

    const totalSpend = result[0]?.totalSpend || 0;
    const totalBudget = totalKeys * KEY_BUDGET;

    // Hiển thị kết quả
    console.log('\n📊 OpenHands Keys Spending Report');
    console.log('================================');
    console.log(`Total Keys:    ${totalKeys}`);
    console.log(`Budget/Key:    $${KEY_BUDGET.toFixed(2)}`);
    console.log(`Total Budget:  $${totalBudget.toFixed(2)}`);
    console.log(`Total Spent:   $${totalSpend.toFixed(2)}`);
    console.log(`Remaining:     $${(totalBudget - totalSpend).toFixed(2)}`);
    console.log(`\n💰 Spending:    $${totalSpend.toFixed(1)}/$${totalBudget.toFixed(0)}`);

    // Chi tiết từng key
    console.log('\n📋 Key Details:');
    console.log('----------------');
    const keys = await collection.find({}).toArray();

    for (let i = 0; i < keys.length; i++) {
      const key = keys[i];
      const remaining = KEY_BUDGET - (key.totalSpend || 0);
      console.log(`  ${i + 1}. ${key._id}: $${(key.totalSpend || 0).toFixed(2)}/$${KEY_BUDGET.toFixed(2)} (remaining: $${remaining.toFixed(2)})`);
    }

  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  } finally {
    await client.close();
  }
}

checkSpend();
