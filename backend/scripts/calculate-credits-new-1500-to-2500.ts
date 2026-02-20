/**
 * Calculate Total CreditsNew and Convert Rate (1500 VND/$1 → 2500 VND/$1)
 *
 * Script này tính tổng creditsNew trong usersNew collection
 * và chuyển đổi từ rate hiện tại (1500 VND/$1) sang rate mới (2500 VND/$1)
 *
 * Công thức: new_credits = old_credits × (1500 / 2500) = old_credits × 0.6
 *
 * Ví dụ: $100 ở rate 1500 VND/$1 = 150,000 VND → $60 ở rate 2500 VND/$1 = 150,000 VND
 *
 * Cách chạy:
 *   npm run calculate:credits-1500-to-2500
 */

import 'dotenv/config';
import mongoose from 'mongoose';

// MongoDB connection - sử dụng environment variable
const uri = process.env.MONGODB_URI;
const dbName = process.env.MONGODB_DB_NAME || 'fproxy';

if (!uri) {
  console.error('❌ MONGODB_URI not set');
  process.exit(1);
}

// Rate constants
const CURRENT_RATE = 1500;  // Rate hiện tại: 1500 VND = $1 USD
const NEW_RATE = 2500;      // Rate mới: 2500 VND = $1 USD

interface UserDocument {
  _id: string;
  creditsNew: number;
  role: string;
}

/**
 * Tính số credits mới khi chuyển đổi rate
 * Công thức: new_credits = old_credits × (current_rate / new_rate)
 * Kết quả làm tròn 2 chữ số thập phân
 */
function calculateNewCredits(oldCredits: number): number {
  const multiplier = CURRENT_RATE / NEW_RATE;
  const newCredits = oldCredits * multiplier;
  return Math.round(newCredits * 100) / 100; // Làm tròn 2 chữ số thập phân
}

async function calculateCreditsNew() {
  try {
    console.log(`🔌 Connecting to MongoDB (database: ${dbName})...`);
    await mongoose.connect(uri, { dbName });

    // Define schema with _id as String (matching UserNew model)
    const userSchema = new mongoose.Schema({
      _id: { type: String, required: true },
      creditsNew: Number,
      role: String,
    }, { strict: false });
    const UserNew = mongoose.model('UserNew', userSchema, 'usersNew');

    console.log('✅ Đã kết nối MongoDB');
    console.log(`📊 Rate hiện tại: ${CURRENT_RATE} VND/$1`);
    console.log(`📊 Rate mới: ${NEW_RATE} VND/$1`);
    console.log(`📊 Hệ số chuyển đổi: ${(CURRENT_RATE / NEW_RATE).toFixed(4)} (${CURRENT_RATE}/${NEW_RATE})\n`);

    // Lấy tất cả users có creditsNew > 0
    const users = await UserNew.find({ creditsNew: { $gt: 0 } })
      .select('_id creditsNew role')
      .sort({ creditsNew: -1 })
      .lean() as UserDocument[];

    console.log(`🔍 Tìm thấy ${users.length} users có creditsNew > 0\n`);

    if (users.length === 0) {
      console.log('Không có user nào có creditsNew. Thoát.');
      return;
    }

    // Tính tổng credits hiện tại
    let totalCurrentCredits = 0;
    let totalNewCredits = 0;

    users.forEach(user => {
      totalCurrentCredits += user.creditsNew;
      totalNewCredits += calculateNewCredits(user.creditsNew);
    });

    // Thống kê theo role
    const adminUsers = users.filter(u => u.role === 'admin');
    const regularUsers = users.filter(u => u.role !== 'admin');

    const adminCurrentTotal = adminUsers.reduce((sum, u) => sum + u.creditsNew, 0);
    const adminNewTotal = adminUsers.reduce((sum, u) => sum + calculateNewCredits(u.creditsNew), 0);
    const regularCurrentTotal = regularUsers.reduce((sum, u) => sum + u.creditsNew, 0);
    const regularNewTotal = regularUsers.reduce((sum, u) => sum + calculateNewCredits(u.creditsNew), 0);

    // Hiển thị top 10 users có creditsNew cao nhất
    console.log('=== TOP 10 USERS CÓ CREDITSNEW CAO NHẤT ===');
    users.slice(0, 10).forEach((user: UserDocument, index: number) => {
      const newCredits = calculateNewCredits(user.creditsNew);
      const vndValue = user.creditsNew * CURRENT_RATE;
      console.log(`  ${index + 1}. ${user._id}`);
      console.log(`     Rate ${CURRENT_RATE}: $${user.creditsNew.toFixed(2)} (${vndValue.toLocaleString('vi-VN')} VND)`);
      console.log(`     Rate ${NEW_RATE}: $${newCredits.toFixed(2)} (${vndValue.toLocaleString('vi-VN')} VND)`);
      console.log(`     Chênh lệch: -$${(user.creditsNew - newCredits).toFixed(2)} (role=${user.role})\n`);
    });

    // Hiển thị tổng kết
    console.log('=== TỔNG KẾT THEO ROLE ===');
    console.log('\n📊 Admin Users:');
    console.log(`   Số lượng: ${adminUsers.length}`);
    console.log(`   Tổng creditsNew hiện tại (rate ${CURRENT_RATE}): $${adminCurrentTotal.toFixed(2)}`);
    console.log(`   Tổng creditsNew sau khi chuyển (rate ${NEW_RATE}): $${adminNewTotal.toFixed(2)}`);
    console.log(`   Giảm: $${(adminCurrentTotal - adminNewTotal).toFixed(2)} (-${(((adminCurrentTotal - adminNewTotal) / adminCurrentTotal) * 100).toFixed(2)}%)`);

    console.log('\n📊 Regular Users:');
    console.log(`   Số lượng: ${regularUsers.length}`);
    console.log(`   Tổng creditsNew hiện tại (rate ${CURRENT_RATE}): $${regularCurrentTotal.toFixed(2)}`);
    console.log(`   Tổng creditsNew sau khi chuyển (rate ${NEW_RATE}): $${regularNewTotal.toFixed(2)}`);
    console.log(`   Giảm: $${(regularCurrentTotal - regularNewTotal).toFixed(2)} (-${(((regularCurrentTotal - regularNewTotal) / regularCurrentTotal) * 100).toFixed(2)}%)`);

    console.log('\n=== TỔNG KẾT CHUNG ===');
    console.log(`📊 Tổng số users: ${users.length}`);
    console.log(`📊 Tổng creditsNew hiện tại (rate ${CURRENT_RATE} VND/$): $${totalCurrentCredits.toFixed(2)}`);
    console.log(`📊 Giá trị VND tương ứng: ${(totalCurrentCredits * CURRENT_RATE).toLocaleString('vi-VN')} VND`);
    console.log(`\n📊 Tổng creditsNew sau khi chuyển (rate ${NEW_RATE} VND/$): $${totalNewCredits.toFixed(2)}`);
    console.log(`📊 Giá trị VND tương ứng: ${(totalNewCredits * NEW_RATE).toLocaleString('vi-VN')} VND`);
    console.log(`\n📊 Chênh lệch: -$${(totalCurrentCredits - totalNewCredits).toFixed(2)}`);
    console.log(`📊 Phần trăm giảm: ${(((totalCurrentCredits - totalNewCredits) / totalCurrentCredits) * 100).toFixed(2)}%`);

    // Phân tích phân bố credits
    console.log('\n=== PHÂN BỐ CREDITSNEW ===');
    const ranges = [
      { min: 0, max: 1, label: '$0-$1' },
      { min: 1, max: 10, label: '$1-$10' },
      { min: 10, max: 50, label: '$10-$50' },
      { min: 50, max: 100, label: '$50-$100' },
      { min: 100, max: 500, label: '$100-$500' },
      { min: 500, max: Infinity, label: '$500+' }
    ];

    ranges.forEach(range => {
      const usersInRange = users.filter(u => u.creditsNew > range.min && u.creditsNew <= range.max);
      const total = usersInRange.reduce((sum, u) => sum + u.creditsNew, 0);
      const totalConverted = usersInRange.reduce((sum, u) => sum + calculateNewCredits(u.creditsNew), 0);

      if (usersInRange.length > 0) {
        console.log(`${range.label}:`);
        console.log(`  Users: ${usersInRange.length}`);
        console.log(`  Tổng hiện tại: $${total.toFixed(2)}`);
        console.log(`  Tổng sau chuyển: $${totalConverted.toFixed(2)}`);
        console.log(`  Giảm: $${(total - totalConverted).toFixed(2)}`);
      }
    });

  } catch (error: any) {
    console.error('❌ Lỗi:', error);
    throw error;
  } finally {
    await mongoose.disconnect();
    console.log('\n🔌 Đã ngắt kết nối MongoDB');
  }
}

console.log('=== TÍNH TOÁN CREDITSNEW (1500 → 2500) ===');
console.log('Script này tính tổng creditsNew và chuyển đổi từ rate 1500 sang 2500 VND/$');
console.log(`Công thức: new_credits = old_credits × (${CURRENT_RATE} / ${NEW_RATE}) = old_credits × ${(CURRENT_RATE / NEW_RATE).toFixed(4)}\n`);

calculateCreditsNew()
  .then(() => {
    console.log('\n✅ Script hoàn thành thành công.');
    process.exit(0);
  })
  .catch((error) => {
    console.error('\n❌ Script thất bại:', error);
    process.exit(1);
  });
