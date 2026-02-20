const { MongoClient } = require('mongodb');
require('dotenv').config({ path: '../.env' });

async function checkBindings() {
  const client = new MongoClient(process.env.MONGODB_URI || 'mongodb+srv://trantai306_db_user:FHBuXtedXaFLBr22@cluster0.aa02bn1.mongodb.net/?appName=Cluster0');

  try {
    await client.connect();
    const db = client.db(process.env.MONGODB_DB_NAME || 'fproxy');

    console.log('=== OhMyGPT Keys ===');
    const keys = await db.collection('ohmygpt_keys').find({}).toArray();
    keys.forEach(k => {
      console.log(`  - ${k._id}: status=${k.status}`);
    });

    console.log('\n=== OhMyGPT Bindings ===');
    const bindings = await db.collection('ohmygpt_bindings').find({}).toArray();
    if (bindings.length === 0) {
      console.log('  (No bindings found - needs setup!)');
    } else {
      bindings.forEach(b => {
        console.log(`  - Proxy ${b.proxyId} -> Key ${b.ohmygptKeyId} (active=${b.isActive})`);
      });
    }

    console.log('\n=== Available Proxies ===');
    const proxies = await db.collection('proxies').find({}).toArray();
    proxies.forEach(p => {
      console.log(`  - ${p._id}: ${p.host}:${p.port}`);
    });
  } finally {
    await client.close();
  }
}

checkBindings();
