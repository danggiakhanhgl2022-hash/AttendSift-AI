# Cài đặt AttendSift AI 1.0.2 trên Windows

## Chọn đúng gói

| Bạn đang có | Cách chạy |
|---|---|
| ZIP có `UngDung/ChamCong.exe` | Giải nén, chạy `KIEM_TRA.bat`, `BAT_DAU.bat`; không cần Python |
| ZIP mã nguồn có `main.py`, `src/` | Cài Python rồi chạy các BAT cài đặt |
| Đường dẫn website | Dùng trình duyệt; dữ liệu cloud không nằm trong SQLite Local |

## Cài từ mã nguồn

1. Cài Python 3.11 x64 từ python.org, bật Python Launcher; cần Internet để tải thư viện.
2. Giải nén vào thư mục có quyền ghi, ví dụ `D:\AttendSift-AI_Source`; tránh Program Files và SQLite trên ổ chia sẻ.
3. Chạy `CAI_DAT_WINDOWS.bat`, đợi thông báo thành công. Môi trường `.venv` được tạo riêng.
4. Chạy `KIEM_TRA_LOCAL_WINDOWS.bat`, rồi `CHAY_LOCAL_WINDOWS.bat`.
5. Mở `http://127.0.0.1:8766` nếu trình duyệt chưa tự mở.
6. Thiết lập token Chatwork, chọn phòng và kiểm tra kết nối AI.
7. Thử tin giả, tạo bảng và đối chiếu Excel 4 sheet trước khi dùng dữ liệu thật.

## Gói portable trên máy người nhận

Xem [hướng dẫn chuyển máy](CHUYEN_MAY_WINDOWS.md). Giải nén toàn bộ gói. EXE chứa Python và thư viện; máy có thể cần WebView2 để mở cửa sổ riêng. Ứng dụng có cơ chế mở trình duyệt local nếu cửa sổ riêng không mở được.

EXE chưa ký số. Khi bị chặn, kiểm tra nguồn nhận, SHA256 và nhờ IT kiểm tra chính sách máy. Checksum không thay thế chứng nhận an toàn độc lập.

## Dữ liệu và chuyển máy

Dữ liệu Local nằm cạnh EXE, hoặc tại gốc mã nguồn khi chạy Python, trong `data`, `outputs`, `backups`, `logs`, `config`. File Excel chính lưu trong Downloads của tài khoản Windows.

Dùng sao lưu/khôi phục để chuyển dữ liệu, đóng ứng dụng và sao lưu máy đích trước khi khôi phục. Nhập lại API key vì khóa Local gắn với tài khoản Windows qua DPAPI. Lưu lại lịch trên máy mới để Task Scheduler dùng đúng đường dẫn.

Chính sách tự xóa 3 tháng chỉ áp dụng cloud. Người vận hành Local tự quản lý sao lưu và thời hạn lưu.

## Khắc phục nhanh

| Hiện tượng | Kiểm tra |
|---|---|
| Không mở hoặc tắt ngay | Giải nén đầy đủ, quyền ghi, `logs/application.log`; chạy kiểm tra môi trường |
| Cổng 8766 đã dùng | Đóng bản cũ; portable có `CHAY_CONG_KHAC.bat` dùng 8767 |
| Không có cửa sổ riêng | Thử trình duyệt local khi EXE còn chạy; kiểm tra WebView2 |
| Không đọc được key sau chuyển máy | Nhập lại trên tài khoản Windows đích |
| Thiếu tin nhắn tháng | Đối chiếu cửa sổ API và nguồn gốc; Local hỗ trợ nhập lịch sử |
| Không thấy Excel | Xem đường dẫn ứng dụng báo và Downloads của tài khoản |
| Excel báo sửa chữa file | Giữ bản đã che dữ liệu để kỹ thuật kiểm tra; chưa xác nhận nghiệm thu |

## Build cho người bảo trì

Build trên Windows bằng `TAO_EXE_WINDOWS.bat` hoặc GitHub Actions. EXE tại `release/ChamCong.exe` phải được kiểm tra runtime và thử trên máy nhận. Xem [quy trình phát hành](PUBLISH_1.0.2.md). Không chép thư mục chứa dữ liệu nhân viên cho người khác.
