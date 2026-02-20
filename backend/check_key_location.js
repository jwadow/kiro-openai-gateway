const { MongoClient } = require('mongodb');

const uri = 'mongodb+srv://trantai306_db_user:FHBuXtedXaFLBr22@cluster0.aa02bn1.mongodb.net/fproxy?appName=Cluster0';

async function checkKey() {
  const client = new MongoClient(uri);
  
  try {
    await client.connect();
    const db = client.db('fproxy');
    
    // Check user_keys collection
    const userKey = await db.collection('user_keys').findOne({ _id: { $regex: '6e94$' } });
    
    console.log('=== user_keys collection ===');
    if (userKey) {
      console.log('Found in user_keys:');
      console.log('  _id:', userKey._id);
      console.log('  name:', userKey.name);
      console.log('  isActive:', userKey.isActive);
    } else {
      console.log('NOT found in user_keys');
    }
    
    // Check usersNew collection
    const usersNewUser = await db.collection('usersNew').findOne({ apiKey: { $regex: '6e94$' } });
    
    console.log('\n=== usersNew collection ===');
    if (usersNewUser) {
      console.log('Found in usersNew:');
      console.log('  _id:', usersNewUser._id);
      console.log('  migration:', usersNewUser.migration);
      console.log('  role:', usersNewUser.role);
    } else {
      console.log('NOT found in usersNew');
    }
    
  } finally {
    await client.close();
  }
}

checkKey();
