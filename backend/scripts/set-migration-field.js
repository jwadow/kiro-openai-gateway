const mongoose = require('mongoose');

// MongoDB connection
const uri = 'mongodb+srv://trantai306_db_user:FHBuXtedXaFLBr22@cluster0.aa02bn1.mongodb.net/fproxy?appName=Cluster0';

async function setMigrationField() {
  try {
    await mongoose.connect(uri);

    // Define schema with strict: false to access all fields
    const userSchema = new mongoose.Schema({}, { strict: false });
    const UserNew = mongoose.model('UserNew', userSchema, 'usersNew');

    console.log('Connected to MongoDB');

    // Check current stats before update
    const noField = await UserNew.countDocuments({ migration: { $exists: false } });
    const alreadyTrue = await UserNew.countDocuments({ migration: true });
    const alreadyFalse = await UserNew.countDocuments({ migration: false });

    console.log('\n=== BEFORE UPDATE ===');
    console.log('No migration field:', noField);
    console.log('Already migrated (true):', alreadyTrue);
    console.log('Already not migrated (false):', alreadyFalse);

    // Set migration=false for users without the field (existing users need to migrate)
    const result = await UserNew.updateMany(
      { migration: { $exists: false } },
      { $set: { migration: false } }
    );

    console.log('\n=== UPDATE RESULT ===');
    console.log('Matched:', result.matchedCount);
    console.log('Modified:', result.modifiedCount);

    // Check stats after update
    const afterNoField = await UserNew.countDocuments({ migration: { $exists: false } });
    const afterFalse = await UserNew.countDocuments({ migration: false });
    const afterTrue = await UserNew.countDocuments({ migration: true });

    console.log('\n=== AFTER UPDATE ===');
    console.log('No migration field:', afterNoField);
    console.log('Not migrated (false):', afterFalse);
    console.log('Migrated (true):', afterTrue);

    // Show some sample users
    const sampleUsers = await UserNew.find(
      {},
      { _id: 1, migration: 1, role: 1, createdAt: 1 }
    ).limit(5);

    console.log('\n=== SAMPLE USERS ===');
    sampleUsers.forEach(u => {
      console.log(`${u._id}: migration=${u.migration}, role=${u.role}`);
    });

  } catch (error) {
    console.error('Error:', error);
  } finally {
    await mongoose.disconnect();
    console.log('\nDisconnected from MongoDB');
  }
}

setMigrationField();
