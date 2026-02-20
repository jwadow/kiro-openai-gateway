/**
 * Create indexes for OhMyGPT collections to improve query performance
 * Run this script to optimize database performance for failover feature
 *
 * Usage:
 *   MONGODB_URI="mongodb+srv://..." node scripts/create-ohmygpt-indexes.js
 *   Or set MONGODB_URI in .env file
 */

const { MongoClient } = require('mongodb');
const dotenv = require('dotenv');

// Load environment variables from .env file
dotenv.config({ path: '../.env' });

const MONGODB_URI = process.env.MONGODB_URI || process.env.MONGO_URI || 'mongodb://localhost:27017/trollllm';

console.log('MongoDB URI:', MONGODB_URI ? 'Set (from environment)' : 'Using default (localhost:27017/trollllm)');
console.log('Make sure MONGODB_URI is set in your environment or .env file for MongoDB Atlas!\n');

async function createIndexes() {
  const client = new MongoClient(MONGODB_URI);

  try {
    await client.connect();
    console.log('✅ Connected to MongoDB');

    const db = client.db();

    // Index for ohmygpt_keys collection
    console.log('\n📋 Creating indexes for ohmygpt_keys collection...');
    await db.collection('ohmygpt_keys').createIndex({ enableFailover: 1 });
    console.log('   ✓ Index on enableFailover');
    await db.collection('ohmygpt_keys').createIndex({ status: 1, enableFailover: 1 });
    console.log('   ✓ Compound index on status + enableFailover');

    // Index for ohmygpt_backup_keys collection
    console.log('\n📋 Creating indexes for ohmygpt_backup_keys collection...');
    await db.collection('ohmygpt_backup_keys').createIndex({ enableFailover: 1 });
    console.log('   ✓ Index on enableFailover');
    await db.collection('ohmygpt_backup_keys').createIndex({ isUsed: 1, enableFailover: 1 });
    console.log('   ✓ Compound index on isUsed + enableFailover');

    // List all indexes to verify
    console.log('\n📊 Indexes created successfully!');
    console.log('\nohmygpt_keys indexes:');
    const keysIndexes = await db.collection('ohmygpt_keys').indexes();
    keysIndexes.forEach(idx => console.log(`   - ${idx.name}`));

    console.log('\nohmygpt_backup_keys indexes:');
    const backupIndexes = await db.collection('ohmygpt_backup_keys').indexes();
    backupIndexes.forEach(idx => console.log(`   - ${idx.name}`));

  } catch (error) {
    console.error('❌ Error creating indexes:', error);
    throw error;
  } finally {
    await client.close();
    console.log('\n✅ Connection closed');
  }
}

createIndexes().then(() => {
  console.log('\n✨ Done!');
  process.exit(0);
}).catch((error) => {
  console.error('\n💥 Script failed:', error);
  process.exit(1);
});
