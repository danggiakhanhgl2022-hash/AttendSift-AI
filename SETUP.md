# Cài đặt AttendSift AI từ mã nguồn

- **Local Windows:** Python 3.11 x64 → chạy `CAI_DAT_WINDOWS.bat`, `KIEM_TRA_LOCAL_WINDOWS.bat`, rồi `CHAY_LOCAL_WINDOWS.bat`; hoặc chạy `python main.py` nếu môi trường đã có dependency phù hợp.
- **Cloud:** cài dependency theo `requirements-web.txt`, cấu hình các biến bí mật theo `.env.example` trong quản lý môi trường của nền tảng. Backend tại `cloud/`; kiểm tra `vercel.json` và hướng dẫn của nền tảng trước khi triển khai.
- **Nhân sự:** không có danh sách cá nhân đi kèm mã nguồn; vào phần quản lý Nhân viên nhập danh sách chính thức riêng. Tên có tên lót sẽ được đối chiếu theo họ tên hồ sơ. Tên quá ngắn khớp nhiều người cần ID xác minh.
- **Xuất Excel:** sử dụng `Cham_cong_*.xlsx` để có năm sheet, không nhầm với export `TinNhan_*.xlsx` chỉ chứa tin nhắn.
- **Kiểm thử:** `python -m pip install -r requirements-dev.txt`; chạy `python -m pytest -q tests/test_public_regressions.py` và `python tools/privacy_audit.py .`. Hãy thử lại bằng dữ liệu giả lập trước khi xử lý dữ liệu thật.

Không commit hoặc đưa bí mật thực vào file ví dụ. Kiểm thử tự động không thay thế việc kiểm chứng bằng ứng dụng Windows, Chatwork/Neon/Vercel và quy trình bảo vệ dữ liệu nội bộ.
