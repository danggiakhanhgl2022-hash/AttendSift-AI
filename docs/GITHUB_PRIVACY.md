# Kiểm tra trước khi tải lên GitHub

1. **Chỉ dùng gói public-source này** làm thư mục repository; không kéo thêm thư mục `data/`, `config/`, `logs/`, `backups/`, `outputs/`, file `.env`, `.db`, `.xlsx` đã xuất, Excel nhân viên, JSON nhân viên riêng, hoặc ZIP gốc.
2. Kiểm tra `.env.example` chỉ có tên biến rỗng. Token Chatwork, database URL Neon, AI API key, session secret, admin password hash và CRON_SECRET phải đặt trong Vercel Environment Variables hoặc thiết lập cá nhân, không lưu Git.
3. Chạy `python tools/privacy_audit.py .`; **sau đó vẫn phải đọc `git diff --cached` và rà soát thủ công** tên nhân viên, khách hàng, email, số điện thoại, ảnh, URL triển khai riêng. Công cụ quét không bảo đảm tìm mọi thông tin nhạy cảm.
4. `git init`, `git add .`, `git status --short`, `git diff --cached --stat`, `git commit -m "Initial public source"`; chỉ kết nối repo GitHub sau khi đã kiểm tra.
5. Nếu bí mật đã từng nằm trong Git history, **xóa khỏi commit mới là chưa đủ**. Cần thu hồi/đổi khóa ngay và dọn lịch sử bằng quy trình có kiểm soát; với kho cũ, an toàn hơn là tạo repository public **mới** từ gói đã lọc.
6. **Không đăng file danh sách 27 nhân viên hoặc Chatwork ID thật.** Nhập trên giao diện quản lý nhân viên sau triển khai, qua kênh riêng có quyền truy cập.

Mã nguồn này không tự đăng lên GitHub hoặc xác nhận tài khoản GitHub đã được cấu hình an toàn.
