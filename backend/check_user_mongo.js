const mongoose = require('mongoose');

const uri = 'mongodb+srv://trantai306_db_user:FHBuXtedXaFLBr22@cluster0.aa02bn1.mongodb.net/fproxy?appName=Cluster0';

async function checkUser() {
  await mongoose.connect(uri);
  const UserNew = mongoose.model('UserNew', new mongoose.Schema({}, { strict: false }), 'usersNew');
  
  const user = await UserNew.findOne(
    { _id: 'thanhdeptrai' }
  ).lean();
  
  console.log('User thanhdeptrai:');
  console.log('  _id:', user._id);
  console.log('  role:', user.role);
  console.log('  migration:', user.migration, '(type:', typeof user.migration, ')');
  console.log('  credits:', user.credits);
  console.log('  apiKey:', user.apiKey ? user.apiKey.substring(0, 15) + '...' : 'none');
  
  await mongoose.disconnect();
}

checkUser();
