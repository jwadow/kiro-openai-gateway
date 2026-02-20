const { MongoClient } = require('mongodb');

const uri = 'mongodb+srv://trantai306_db_user:FHBuXtedXaFLBr22@cluster0.aa02bn1.mongodb.net/fproxy?appName=Cluster0';

async function checkUser() {
  const client = new MongoClient(uri);
  
  try {
    await client.connect();
    const db = client.db('fproxy');
    const usersNew = db.collection('usersNew');
    
    const user = await usersNew.findOne({ _id: 'thanhdeptrai' });
    
    console.log('User thanhdeptrai:');
    console.log('  _id:', user._id);
    console.log('  role:', user.role);
    console.log('  migration:', user.migration, '(type:', typeof user.migration, ')');
    console.log('  credits:', user.credits);
    console.log('  isActive:', user.isActive);
    
  } finally {
    await client.close();
  }
}

checkUser();
