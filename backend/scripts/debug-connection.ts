import 'dotenv/config';
import mongoose from 'mongoose';

async function debugConnection() {
  try {
    const uri = process.env.MONGODB_URI;
    const dbName = process.env.MONGODB_DB_NAME || 'fproxy';

    console.log('🔍 MONGODB_URI:', uri);
    console.log('🔍 MONGODB_DB_NAME:', dbName);

    if (!uri) {
      throw new Error('MONGODB_URI not found');
    }

    console.log('\n🔌 Connecting to MongoDB...');
    await mongoose.connect(uri, { dbName });
    console.log('✅ Connected!');

    // Lấy database name hiện tại
    const dbName = mongoose.connection.db.databaseName;
    console.log(`\n📊 Current database: ${dbName}`);

    // Liệt kê tất cả collections
    console.log('\n=== ALL COLLECTIONS IN DATABASE ===');
    const collections = await mongoose.connection.db.listCollections().toArray();

    if (collections.length === 0) {
      console.log('❌ No collections found!');
    } else {
      collections.forEach((col: any, i: number) => {
        console.log(`${i + 1}. ${col.name} (type: ${col.type})`);
      });
    }

    // Tìm collection có tên tương tự users
    console.log('\n=== COLLECTIONS CONTAINING "user" ===');
    const userCollections = collections.filter((col: any) =>
      col.name.toLowerCase().includes('user')
    );

    if (userCollections.length === 0) {
      console.log('❌ No user-related collections found!');
    } else {
      for (const col of userCollections) {
        const count = await mongoose.connection.db.collection(col.name).countDocuments();
        console.log(`- ${col.name}: ${count} documents`);

        // Lấy 1 document mẫu
        const sample = await mongoose.connection.db.collection(col.name).findOne({});
        if (sample) {
          console.log(`  Sample fields: ${Object.keys(sample).join(', ')}`);
        }
      }
    }

    // Kiểm tra cụ thể collection usersNew
    console.log('\n=== CHECKING "usersNew" COLLECTION ===');
    try {
      const usersNewCount = await mongoose.connection.db.collection('usersNew').countDocuments();
      console.log(`usersNew collection: ${usersNewCount} documents`);
    } catch (err: any) {
      console.log(`❌ Error accessing usersNew: ${err.message}`);
    }

    await mongoose.disconnect();
    console.log('\n🔌 Disconnected');
  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  }
}

debugConnection();
