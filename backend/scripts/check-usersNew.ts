import 'dotenv/config';
import mongoose from 'mongoose';

async function checkUsersNew() {
  try {
    const uri = process.env.MONGODB_URI;
    const dbName = process.env.MONGODB_DB_NAME || 'fproxy';

    if (!uri) {
      throw new Error('MONGODB_URI not found');
    }

    console.log(`🔌 Connecting to MongoDB (database: ${dbName})...`);
    await mongoose.connect(uri, { dbName });
    console.log('✅ Connected!\n');

    const UserNew = mongoose.model('UserNew', new mongoose.Schema({}, { strict: false }), 'usersNew');

    // Đếm tổng số documents
    const totalCount = await UserNew.countDocuments();
    console.log(`📊 Tổng số documents trong usersNew: ${totalCount}\n`);

    if (totalCount === 0) {
      console.log('❌ Collection usersNew trống!');
      await mongoose.disconnect();
      return;
    }

    // Lấy 5 documents mẫu để xem cấu trúc
    console.log('=== 5 DOCUMENTS MẪU ===');
    const sampleUsers = await UserNew.find({}).limit(5).lean();
    sampleUsers.forEach((user: any, i: number) => {
      console.log(`\n${i + 1}. User: ${user._id}`);
      console.log(`   credits: ${user.credits || 0}`);
      console.log(`   creditsNew: ${user.creditsNew || 0}`);
      console.log(`   creditsUsed: ${user.creditsUsed || 0}`);
      console.log(`   creditsNewUsed: ${user.creditsNewUsed || 0}`);
      console.log(`   role: ${user.role || 'N/A'}`);
      console.log(`   migration: ${user.migration}`);
    });

    // Thống kê creditsNew
    console.log('\n\n=== THỐNG KÊ CREDITSNEW ===');
    const withCreditsNew = await UserNew.countDocuments({ creditsNew: { $gt: 0 } });
    const withZeroCreditsNew = await UserNew.countDocuments({ creditsNew: 0 });
    const withNullCreditsNew = await UserNew.countDocuments({ creditsNew: { $exists: false } });

    console.log(`Users có creditsNew > 0: ${withCreditsNew}`);
    console.log(`Users có creditsNew = 0: ${withZeroCreditsNew}`);
    console.log(`Users không có field creditsNew: ${withNullCreditsNew}`);

    // Thống kê credits (OhMyGPT)
    console.log('\n=== THỐNG KÊ CREDITS (OhMyGPT) ===');
    const withCredits = await UserNew.countDocuments({ credits: { $gt: 0 } });
    const withZeroCredits = await UserNew.countDocuments({ credits: 0 });

    console.log(`Users có credits > 0: ${withCredits}`);
    console.log(`Users có credits = 0: ${withZeroCredits}`);

    // Tổng credits và creditsNew
    const allUsers = await UserNew.find({}).select('credits creditsNew').lean();
    const totalCredits = allUsers.reduce((sum: number, u: any) => sum + (u.credits || 0), 0);
    const totalCreditsNew = allUsers.reduce((sum: number, u: any) => sum + (u.creditsNew || 0), 0);

    console.log(`\nTổng credits (OhMyGPT): $${totalCredits.toFixed(2)}`);
    console.log(`Tổng creditsNew (OpenHands): $${totalCreditsNew.toFixed(2)}`);

    // Tìm user có creditsNew cao nhất (nếu có)
    if (withCreditsNew > 0) {
      console.log('\n=== TOP 10 USERS CÓ CREDITSNEW CAO NHẤT ===');
      const topUsers = await UserNew.find({ creditsNew: { $gt: 0 } })
        .sort({ creditsNew: -1 })
        .limit(10)
        .lean();

      topUsers.forEach((user: any, i: number) => {
        console.log(`${i + 1}. ${user._id}: $${(user.creditsNew || 0).toFixed(2)}`);
      });
    }

    // Tìm user có credits cao nhất
    if (withCredits > 0) {
      console.log('\n=== TOP 10 USERS CÓ CREDITS CAO NHẤT ===');
      const topUsers = await UserNew.find({ credits: { $gt: 0 } })
        .sort({ credits: -1 })
        .limit(10)
        .lean();

      topUsers.forEach((user: any, i: number) => {
        console.log(`${i + 1}. ${user._id}: $${(user.credits || 0).toFixed(2)}`);
      });
    }

    await mongoose.disconnect();
    console.log('\n🔌 Disconnected from MongoDB');
  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  }
}

checkUsersNew();
