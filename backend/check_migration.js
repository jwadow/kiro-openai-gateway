const mongoose = require('mongoose');

const uri = process.env.MONGODB_URI || 'mongodb://localhost:27017/trollllm';

async function checkMigration() {
  try {
    await mongoose.connect(uri);
    const UserNew = mongoose.model('UserNew', new mongoose.Schema({}, { strict: false }), 'usersNew');
    
    // Check migration status for thanhdeptrai
    const user = await UserNew.findOne(
      { _id: 'thanhdeptrai' },
      { _id: 1, migration: 1, credits: 1, role: 1, apiKey: 1 }
    ).lean();
    
    if (user) {
      console.log('User thanhdeptrai:');
      console.log('  migration:', user.migration);
      console.log('  credits:', user.credits);
      console.log('  role:', user.role);
      console.log('  apiKey:', user.apiKey ? user.apiKey.substring(0, 20) + '...' : 'none');
    } else {
      console.log('User thanhdeptrai not found');
    }
    
    // Count users by migration status
    const migrated = await UserNew.countDocuments({ migration: true });
    const notMigrated = await UserNew.countDocuments({ migration: false });
    const noField = await UserNew.countDocuments({ migration: { $exists: false } });
    
    console.log('\nMigration stats:');
    console.log('  migrated (migration=true):', migrated);
    console.log('  not migrated (migration=false):', notMigrated);
    console.log('  no migration field:', noField);
    
  } finally {
    await mongoose.disconnect();
  }
}

checkMigration();
