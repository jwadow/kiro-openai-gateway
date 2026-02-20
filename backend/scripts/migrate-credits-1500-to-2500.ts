/**
 * Credit Rate Migration Script (1500 VND/$1 → 2500 VND/$1)
 *
 * Script này migrate creditsNew của users từ rate cũ (1500 VND/$1)
 * sang rate mới (2500 VND/$1), bảo toàn giá trị VND của credits.
 *
 * Công thức: new_credits = old_credits × (1500 / 2500) = old_credits × 0.6
 *
 * Ví dụ: $100 ở 1500 VND/$1 = 150,000 VND → $60 ở 2500 VND/$1 = 150,000 VND
 *
 * Cách dùng:
 *   npm run migrate:1500-to-2500             # Dry-run mode (mặc định, chỉ xem preview)
 *   npm run migrate:1500-to-2500 -- --apply  # Apply mode (thực hiện migration)
 *   npm run migrate:1500-to-2500 -- --apply --include-admins  # Bao gồm cả admin accounts
 *
 * Tính năng:
 *   - Dry-run mode để test an toàn
 *   - Idempotent (an toàn khi chạy lại, tự động bỏ qua users đã migrate)
 *   - Atomic updates từng user
 *   - Ghi log đầy đủ vào migration_logs collection
 *   - Không thay đổi refCredits
 */

import 'dotenv/config';
import mongoose from 'mongoose';

// MongoDB connection
const uri = process.env.MONGODB_URI;
const dbName = process.env.MONGODB_DB_NAME || 'fproxy';

if (!uri) {
  console.error('❌ MONGODB_URI not set');
  process.exit(1);
}

// Migration constants
const OLD_RATE = 1500;  // Rate cũ: 1500 VND = $1 USD
const NEW_RATE = 2500;  // Rate mới: 2500 VND = $1 USD
const SCRIPT_VERSION = '1500-to-2500';

interface MigrationLog {
  userId: string;
  username: string;
  oldCredits: number;
  newCredits: number;
  migratedAt: Date;
  oldRate: number;
  newRate: number;
  scriptVersion: string;
  appliedBy: string;
  notes: string;
}

interface UserDocument {
  _id: string;
  creditsNew: number;
  refCredits: number;
  role: string;
}

/**
 * Tính số credits mới sử dụng công thức chuyển đổi rate
 * Công thức: new_credits = old_credits × (old_rate / new_rate)
 * Kết quả làm tròn 2 chữ số thập phân (cents precision)
 */
function calculateNewCredits(oldCredits: number): number {
  const multiplier = OLD_RATE / NEW_RATE;
  const newCredits = oldCredits * multiplier;
  return Math.round(newCredits * 100) / 100; // Làm tròn 2 chữ số thập phân
}

async function migrateCredits(dryRun: boolean = true, includeAdmins: boolean = false) {
  try {
    console.log(`🔌 Connecting to MongoDB (database: ${dbName})...`);
    await mongoose.connect(uri, { dbName });

    // Define schema với _id là String (matching UserNew model)
    const userSchema = new mongoose.Schema({
      _id: { type: String, required: true },
      creditsNew: Number,
      refCredits: Number,
      role: String,
    }, { strict: false });
    const UserNew = mongoose.model('UserNew', userSchema, 'usersNew');

    console.log('✅ Connected to MongoDB');
    console.log(`📊 Mode: ${dryRun ? 'DRY RUN (không có thay đổi nào được thực hiện)' : 'APPLY (thực hiện migration)'}`);
    console.log(`📊 Admin accounts: ${includeAdmins ? 'BAO GỒM' : 'LOẠI TRỪ'}`);

    // Tìm users cần migrate
    // 1. Users có creditsNew > 0
    // 2. Users chưa có migration log với scriptVersion: "1500-to-2500"

    // Lấy danh sách user IDs đã được migrate
    const migratedUserIds = await mongoose.connection
      .collection('migration_logs')
      .find({ scriptVersion: SCRIPT_VERSION })
      .project({ userId: 1 })
      .toArray();

    const migratedSet = new Set(migratedUserIds.map((doc: any) => doc.userId));

    // Build query cho users cần migrate
    const query: any = {
      creditsNew: { $gt: 0 },
      _id: { $nin: Array.from(migratedSet) }
    };

    // Loại trừ admins theo mặc định
    if (!includeAdmins) {
      query.role = { $ne: 'admin' };
    }

    const affectedUsers = await UserNew.find(query)
      .select('_id creditsNew refCredits role')
      .sort({ _id: 1 })
      .lean() as UserDocument[];

    console.log('\n=== USERS CẦN MIGRATE ===');
    console.log(`🔍 Tìm thấy ${affectedUsers.length} users cần migration`);

    if (affectedUsers.length === 0) {
      console.log('✅ Không có users nào cần migrate. Thoát.');
      return;
    }

    // Tính thống kê
    let totalOldCredits = 0;
    let totalNewCredits = 0;

    affectedUsers.forEach(user => {
      totalOldCredits += user.creditsNew;
      totalNewCredits += calculateNewCredits(user.creditsNew);
    });

    // Hiển thị 10 users đầu tiên
    console.log('\n=== MẪU USERS (10 đầu tiên) ===');
    affectedUsers.slice(0, 10).forEach((user: UserDocument) => {
      const newCredits = calculateNewCredits(user.creditsNew);
      const vndValue = user.creditsNew * OLD_RATE;
      console.log(`  - ${user._id}:`);
      console.log(`    Rate ${OLD_RATE}: $${user.creditsNew.toFixed(2)} (${vndValue.toLocaleString('vi-VN')} VND)`);
      console.log(`    Rate ${NEW_RATE}: $${newCredits.toFixed(2)} (${vndValue.toLocaleString('vi-VN')} VND)`);
      console.log(`    Role: ${user.role}, RefCredits: $${user.refCredits || 0}`);
    });

    if (affectedUsers.length > 10) {
      console.log(`  ... và ${affectedUsers.length - 10} users nữa`);
    }

    // Hiển thị tổng kết
    console.log('\n=== PREVIEW MIGRATION ===');
    console.log(`Tổng số users: ${affectedUsers.length}`);
    console.log(`Tổng creditsNew trước: $${totalOldCredits.toFixed(2)} (rate ${OLD_RATE})`);
    console.log(`Tổng creditsNew sau: $${totalNewCredits.toFixed(2)} (rate ${NEW_RATE})`);
    console.log(`Giảm: $${(totalOldCredits - totalNewCredits).toFixed(2)} (-${(((totalOldCredits - totalNewCredits) / totalOldCredits) * 100).toFixed(2)}%)`);
    console.log(`Giá trị VND được bảo toàn: ${(totalOldCredits * OLD_RATE).toLocaleString('vi-VN')} VND`);

    if (dryRun) {
      console.log('\n=== DRY RUN HOÀN THÀNH ===');
      console.log('Để thực hiện migration, chạy lệnh: npm run migrate:1500-to-2500 -- --apply');
    } else {
      // Thực hiện migration
      console.log('\n=== BẮT ĐẦU MIGRATION ===');

      let successCount = 0;
      let skippedZeroCredits = 0;
      let failedCount = 0;

      for (const user of affectedUsers) {
        try {
          // Skip users có zero credits (không nên xảy ra do query, nhưng safety check)
          if (user.creditsNew === 0) {
            skippedZeroCredits++;
            console.log(`  ⊘ Bỏ qua: ${user._id} (zero credits)`);
            continue;
          }

          const oldCredits = user.creditsNew;
          const newCredits = calculateNewCredits(oldCredits);

          // Update user creditsNew atomically
          const updateResult = await mongoose.connection.collection('usersNew').updateOne(
            { _id: user._id },
            { $set: { creditsNew: newCredits } }
          );

          if (updateResult.modifiedCount === 0) {
            throw new Error('Update không thay đổi document nào');
          }

          // Tạo migration log
          await mongoose.connection.collection('migration_logs').insertOne({
            userId: user._id,
            username: user._id,
            oldCredits: oldCredits,
            newCredits: newCredits,
            migratedAt: new Date(),
            oldRate: OLD_RATE,
            newRate: NEW_RATE,
            scriptVersion: SCRIPT_VERSION,
            appliedBy: 'admin',
            notes: `Automatic rate migration from ${OLD_RATE} to ${NEW_RATE} VND/$`
          } as MigrationLog);

          successCount++;
          if (successCount <= 10 || successCount % 50 === 0) {
            console.log(`  ✓ Migrated: ${user._id} ($${oldCredits.toFixed(2)} → $${newCredits.toFixed(2)})`);
          }
        } catch (error: any) {
          failedCount++;
          console.error(`  ✗ Failed: ${user._id} - ${error.message}`);
        }
      }

      console.log('\n=== TỔNG KẾT MIGRATION ===');
      console.log(`Tổng số users xử lý: ${affectedUsers.length}`);
      console.log(`✓ Thành công: ${successCount}`);
      if (skippedZeroCredits > 0) {
        console.log(`⊘ Bỏ qua (zero credits): ${skippedZeroCredits}`);
      }
      if (failedCount > 0) {
        console.log(`✗ Thất bại: ${failedCount}`);
      }

      // Tính tổng thực tế
      const actualOldTotal = affectedUsers.slice(0, successCount).reduce((sum, u) => sum + u.creditsNew, 0);
      const actualNewTotal = affectedUsers.slice(0, successCount).reduce((sum, u) => sum + calculateNewCredits(u.creditsNew), 0);

      console.log(`\n📊 Tổng creditsNew trước: $${actualOldTotal.toFixed(2)}`);
      console.log(`📊 Tổng creditsNew sau: $${actualNewTotal.toFixed(2)}`);
      console.log(`📊 Giảm: $${(actualOldTotal - actualNewTotal).toFixed(2)} (-${(((actualOldTotal - actualNewTotal) / actualOldTotal) * 100).toFixed(2)}%)`);

      // Kiểm tra còn users nào chưa migrate
      const stillMigrated = await mongoose.connection
        .collection('migration_logs')
        .find({ scriptVersion: SCRIPT_VERSION })
        .count();

      const remainingQuery: any = {
        creditsNew: { $gt: 0 }
      };
      if (!includeAdmins) {
        remainingQuery.role = { $ne: 'admin' };
      }

      const remaining = await UserNew.countDocuments(remainingQuery) - stillMigrated;

      console.log(`\n📊 Users chưa migrate còn lại: ${remaining}`);
    }

  } catch (error: any) {
    console.error('❌ Lỗi:', error);
    throw error;
  } finally {
    await mongoose.disconnect();
    console.log('\n🔌 Đã ngắt kết nối MongoDB');
  }
}

// Parse command line arguments
const args = process.argv.slice(2);
const dryRun = !args.includes('--apply');
const includeAdmins = args.includes('--include-admins');

console.log('=== Credit Rate Migration Script (1500 → 2500) ===');
console.log('Script này chuyển đổi creditsNew của users để bảo toàn giá trị VND.');
console.log(`Công thức: new_credits = old_credits × (${OLD_RATE} / ${NEW_RATE}) = old_credits × ${(OLD_RATE / NEW_RATE).toFixed(4)}\n`);

migrateCredits(dryRun, includeAdmins)
  .then(() => {
    console.log('\n✅ Script hoàn thành thành công.');
    process.exit(0);
  })
  .catch((error) => {
    console.error('\n❌ Script thất bại:', error);
    process.exit(1);
  });
