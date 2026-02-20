const { MongoClient } = require('mongodb');
require('dotenv').config({ path: '../.env' });

async function setupOhMyGPTBindings() {
  const client = new MongoClient(process.env.MONGODB_URI || 'mongodb+srv://trantai306_db_user:FHBuXtedXaFLBr22@cluster0.aa02bn1.mongodb.net/?appName=Cluster0');

  try {
    await client.connect();
    const db = client.db(process.env.MONGODB_DB_NAME || 'fproxy');

    // Get OhMyGPT key
    const ohmygptKey = await db.collection('ohmygpt_keys').findOne({ _id: 'ohmygpt-test-001' });
    if (!ohmygptKey) {
      console.error('❌ OhMyGPT key not found! Run add-ohmygpt-test-key.js first.');
      return;
    }

    // Get available proxies
    const proxies = await db.collection('proxies').find({}).toArray();
    console.log(`Found ${proxies.length} proxies`);

    // Create bindings for all proxies
    for (const proxy of proxies) {
      const binding = {
        proxyId: proxy._id.toString(),
        ohmygptKeyId: 'ohmygpt-test-001',
        priority: 1,
        isActive: true,
        createdAt: new Date()
      };

      // Check if binding already exists
      const existing = await db.collection('ohmygpt_bindings').findOne({
        proxyId: binding.proxyId
      });

      if (existing) {
        console.log(`⚠️  Binding for ${proxy._id} already exists, updating...`);
        await db.collection('ohmygpt_bindings').updateOne(
          { proxyId: binding.proxyId },
          { $set: binding }
        );
      } else {
        await db.collection('ohmygpt_bindings').insertOne(binding);
        console.log(`✅ Created binding: ${proxy._id} -> ohmygpt-test-001`);
      }
    }

    console.log('\n=== OhMyGPT Bindings Summary ===');
    const bindings = await db.collection('ohmygpt_bindings').find({ isActive: true }).toArray();
    console.log(`Total active bindings: ${bindings.length}`);
    bindings.forEach(b => {
      console.log(`  - ${b.proxyId} -> ${b.ohmygptKeyId}`);
    });

  } finally {
    await client.close();
  }
}

setupOhMyGPTBindings();
