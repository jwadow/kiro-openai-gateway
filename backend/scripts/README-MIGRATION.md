# Credit Rate Migration Scripts

## Tổng quan

Các scripts này giúp migrate và tính toán credits khi thay đổi exchange rate giữa VND và USD.

## Scripts có sẵn

### 1. Kiểm tra usersNew collection
```bash
npm run check:users-new
```
Hiển thị:
- Tổng số documents
- Sample documents với cấu trúc fields
- Thống kê creditsNew và credits
- Top 10 users có credits cao nhất

### 2. Tính toán credits với rate mới (1500 → 2500)
```bash
npm run calculate:credits-1500-to-2500
```
Hiển thị preview về:
- Tổng creditsNew hiện tại ở rate 1500 VND/$
- Tổng creditsNew nếu chuyển sang rate 2500 VND/$
- Top 10 users có creditsNew cao nhất
- Thống kê theo role (Admin vs Regular)
- Phân bố credits theo khoảng giá trị

**Lưu ý**: Script này CHỈ TÍNH TOÁN, không thay đổi database.

### 3. Migration credits (1500 → 2500) - CHÚ Ý!
```bash
# Dry-run mode (mặc định) - Chỉ xem preview, KHÔNG thay đổi database
npm run migrate:1500-to-2500

# Apply mode - THỰC HIỆN migration (THAY ĐỔI DATABASE!)
npm run migrate:1500-to-2500 -- --apply

# Bao gồm cả admin accounts
npm run migrate:1500-to-2500 -- --apply --include-admins
```

## Công thức chuyển đổi

### Rate 1500 → 2500 VND/$
```
new_credits = old_credits × (1500 / 2500) = old_credits × 0.6
```

**Ví dụ**:
- $100 ở rate 1500 VND/$ = 150,000 VND
- $60 ở rate 2500 VND/$ = 150,000 VND
- **Giá trị VND được bảo toàn!**

### Rate 2500 → 1500 VND/$
```
new_credits = old_credits × (2500 / 1500) = old_credits × 1.6667
```

## Quy trình Migration an toàn

### Bước 1: Kiểm tra dữ liệu hiện tại
```bash
npm run check:users-new
```

### Bước 2: Xem preview migration
```bash
npm run calculate:credits-1500-to-2500
```
Hoặc
```bash
npm run migrate:1500-to-2500  # Dry-run mode
```

### Bước 3: Backup database (QUAN TRỌNG!)
```bash
# Sử dụng mongodump hoặc MongoDB Atlas backup
mongodump --uri="your-mongodb-uri" --db=fproxy --out=backup-$(date +%Y%m%d)
```

### Bước 4: Thực hiện migration
```bash
npm run migrate:1500-to-2500 -- --apply
```

### Bước 5: Verify kết quả
```bash
npm run check:users-new
```

## Tính năng an toàn

### 1. Dry-run mode mặc định
- Mặc định scripts chạy ở chế độ preview
- Phải có flag `--apply` mới thực hiện thay đổi

### 2. Idempotent (an toàn khi chạy lại)
- Scripts tự động bỏ qua users đã được migrate
- Ghi log vào collection `migration_logs`
- Có thể chạy lại nhiều lần mà không lo bị duplicate

### 3. Atomic updates
- Mỗi user được update riêng lẻ
- Nếu có lỗi, chỉ user đó bị ảnh hưởng

### 4. Migration logs
Mỗi migration được ghi log vào collection `migration_logs`:
```javascript
{
  userId: string,
  username: string,
  oldCredits: number,
  newCredits: number,
  migratedAt: Date,
  oldRate: number,
  newRate: number,
  scriptVersion: string, // "1500-to-2500" hoặc "2500-to-1500"
  appliedBy: string,
  notes: string
}
```

## Rollback

Nếu cần rollback, chạy script ngược lại:

```bash
# Nếu đã migrate từ 1500 → 2500, rollback bằng cách:
npm run migrate:2500-to-1500 -- --apply
```

**LƯU Ý**: Rollback chỉ hoàn hảo nếu không có transactions mới trong thời gian migrate.

## Troubleshooting

### Lỗi: "Collection usersNew trống"
Kiểm tra MONGODB_URI và MONGODB_DB_NAME trong file `.env`:
```bash
MONGODB_URI=mongodb+srv://...
MONGODB_DB_NAME=fproxy
```

### Lỗi: "Cannot find module"
Cài đặt dependencies:
```bash
npm install
```

### Script chạy lâu quá
Đây là bình thường nếu có nhiều users. Script hiển thị progress mỗi 50 users.

## Câu hỏi thường gặp

**Q: Script có thay đổi refCredits không?**
A: KHÔNG. Script chỉ thay đổi creditsNew, refCredits được giữ nguyên.

**Q: Admin accounts có được migrate không?**
A: Mặc định KHÔNG. Dùng flag `--include-admins` nếu cần.

**Q: Có thể chạy lại script nhiều lần không?**
A: CÓ. Script tự động bỏ qua users đã migrate.

**Q: Có cần backup không?**
A: KHUYẾN NGHỊ backup trước khi apply migration.

**Q: Giá trị VND có thay đổi không?**
A: KHÔNG. Công thức được thiết kế để bảo toàn giá trị VND.
