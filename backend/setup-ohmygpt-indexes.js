const { MongoClient } = require('mongodb');
require('dotenv').config({ path: '.env' });

const MONGODB_URI = process.env.MONGODB_URI || 'mongodb+srv://trantai306_db_user:FHBuXtedXaFLBr22@cluster0.aa02bn1.mongodb.net/?appName=Cluster0';
const DB_NAME = process.env.MONGODB_DB_NAME || 'fproxy';

async function setupIndexes() {
  const client = new MongoClient(MONGODB_URI);

  try {
    await client.connect();
    console.log('✅ Connected to MongoDB');

    const db = client.db(DB_NAME);

    // Create indexes for ohmygpt_keys collection
    console.log('Creating indexes for ohmygpt_keys...');
    await db.collection('ohmygpt_keys').createIndex({ "status": 1 });
    await db.collection('ohmygpt_keys').createIndex({ "cooldownUntil": 1 });
    await db.collection('ohmygpt_keys').createIndex({ "createdAt": -1 });
    console.log('✅ ohmygpt_keys indexes created');

    // Create indexes for ohmygpt_bindings collection
    console.log('Creating indexes for ohmygpt_bindings...');
    await db.collection('ohmygpt_bindings').createIndex({ "proxyId": 1, "isActive": 1 });
    await db.collection('ohmygpt_bindings').createIndex({ "ohmygptKeyId": 1 });
    console.log('✅ ohmygpt_bindings indexes created');

    // Create index for ohmygpt_backup_keys collection
    console.log('Creating indexes for ohmygpt_backup_keys...');
    await db.collection('ohmygpt_backup_keys').createIndex({ "isUsed": 1 });
    console.log('✅ ohmygpt_backup_keys indexes created');

    console.log('');
    console.log('✅ All OhMyGPT database indexes created successfully!');
  } catch (error) {
    console.error('❌ Error:', error);
  } finally {
    await client.close();
  }
}

setupIndexes();
