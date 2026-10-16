# Đưa dự án lên GitHub và tạo Windows EXE

## 1. Tạo repository PRIVATE

Vào GitHub > **New repository** > tên ví dụ `ChamCongChatwork` > chọn **Private** > **Create repository**. Không upload thư mục `data`, `.credentials`, `.env`, file Excel nhân viên hoặc logs. README và `.gitignore` đã có trong gói này.

## 2. Từ thư mục đã giải nén, dùng Git

Mở **Git Bash** hoặc PowerShell tại thư mục chứa `README.md` rồi chạy:

```bash
git init
git add .
git status
git commit -m "Prepare Windows Local GitHub release"
git branch -M main
git remote add origin https://github.com/<USER>/<REPOSITORY>.git
git push -u origin main
```

Thay `<USER>` và `<REPOSITORY>` bằng thông tin trên GitHub. Nếu GitHub yêu cầu xác thực, sử dụng trình đăng nhập Git Credential Manager hoặc phương thức xác thực GitHub hỗ trợ, **không đặt token vào URL rồi commit**. Dùng `git status` kiểm tra trước khi push.

## 3. Lấy EXE tự động từ GitHub Actions

Vào tab **Actions** > workflow **Source checks and Windows Local build** > chọn run trên nhánh `main`. Nếu chưa chạy, chọn **Run workflow**. Khi job **windows-local** thành công, mở run > **Artifacts** > `ChamCong-Windows-EXE` và tải xuống. Giải nén `ChamCong.exe`, đặt trong thư mục có quyền ghi trên máy Windows khác. Mở EXE để ứng dụng hoạt động độc lập với Python nếu thư viện và runtime Windows tương thích.

**EXE xây bằng GitHub Actions hiện mới là cấu hình build được chuẩn bị, chưa có kết quả thực tế từ Windows runner trong phiên này.** Kiểm tra ứng dụng và Excel trên Windows thật trước khi phát cho người dùng.

## 4. Cập nhật mã từ máy khác

- Nếu muốn lấy mã mới: clone repository, hoặc tải ZIP từ GitHub rồi giải nén tại máy mới.
- Nếu muốn chạy giao diện trình duyệt Local: dùng `CAI_DAT_WINDOWS.bat` rồi `CHAY_LOCAL_WINDOWS.bat`.
- Mỗi máy mặc định có cơ sở dữ liệu SQLite riêng. Dùng database chung chỉ khi bạn triển khai hệ thống Web/PostgreSQL trung tâm.
