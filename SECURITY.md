# Bảo mật và dữ liệu chấm công

- **Mặc định tạo repository GitHub ở chế độ PRIVATE.** Kiểm tra kỹ fixture, tên nhân viên và văn bản trong `tests/` trước khi cân nhắc PUBLIC.
- Không commit/đẩy lên GitHub: `.env` thật, API key, mật khẩu, `data/*.db`, `*.credentials`, `config`, `logs`, `outputs`, `backups`, file Excel thực tế, ảnh chụp màn hình có nhân sự.
- `.gitignore` chỉ ngăn theo đường dẫn: **nếu từng lỡ commit secret, phải xóa khỏi Git history và thu hồi/đổi ngay API key**. Không chỉ xóa file rồi commit.
- Local mặc định chỉ lắng nghe `127.0.0.1`, **không mở port 8766 ra LAN/Internet**.
- Khóa API trên Windows lưu theo DPAPI của máy/tài khoản. Khi chuyển máy, nhập lại khóa trên máy mới; không chia sẻ `.credentials`.
- Thiết lập bảo mật của bản hosting Web (PostgreSQL + tài khoản admin + allowed hosts) **khác** bản chạy Local.
- Dùng dữ liệu giả trong kiểm thử công khai; không đưa tin nhắn nhân viên thật vào Issue, Actions Log hay PR.
- Cập nhật thư viện định kỳ và chỉ dùng repo/EXE tải từ nguồn đáng tin cậy. Kiểm tra antivirus trước khi chạy EXE mới.
