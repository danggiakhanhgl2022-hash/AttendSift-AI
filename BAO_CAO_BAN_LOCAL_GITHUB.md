# Báo cáo chuyển dự án thành GitHub + Windows Local

## Mục tiêu

- Dùng **một mã nguồn** cho Windows Local và có lựa chọn triển khai cloud riêng (`app.py`, `cloud/`).
- Người dùng Windows khác có thể tải GitHub ZIP, cài Python 3.11/3.12, chạy script rồi mở `127.0.0.1:8766`.
- Nếu cần EXE không phải cài Python ở máy nhận, build trên **Windows** từ `TAO_EXE_WINDOWS.bat` hoặc workflow GitHub Actions.
- Khi chạy Local **không cần Postgres**. SQLite nằm trong `data/` tại máy đó; mỗi máy mặc định dùng một DB riêng.

## Đã thay đổi

1. Loại khỏi bộ phát hành dữ liệu và bí mật: SQLite, khóa DPAPI, logs, backups, file Excel kết quả, duplicate deploy bundle.
2. Đường khởi chạy Windows Local: `CAI_DAT_WINDOWS.bat`, `CHAY_LOCAL_WINDOWS.bat`, `KIEM_TRA_LOCAL_WINDOWS.bat`.
3. Công cụ build EXE tại máy Windows: `TAO_EXE_WINDOWS.bat` (dùng PyInstaller).
4. Bổ sung README, tài liệu chuyển máy, .gitignore/.gitattributes, SECURITY.md, CI tự động kiểm tra mã nguồn và tạo Windows EXE.
5. Sửa mặc định không loại Cầm/Ny/Tráng nếu tên không được gắn `(CTV)` hoặc không được người sử dụng xác nhận rõ qua `CHAMCONG_CTV_ALIASES`.
6. Phần chấm công OT vẫn tách theo **ngày × người × loại sự kiện**, mỗi người được ghi toàn bộ thời lượng của riêng họ. Phép năm, người có `(CTV)` chỉ lưu tin gốc theo yêu cầu.

## Kết quả đã xác minh trong môi trường hiện tại

- 34/34 kiểm thử chủ đích về chính sách, nhóm OT, giữ tin gốc, định dạng Downloads và cấu trúc Local đạt.
- `compileall` cho Python nguồn chạy thành công.
- Kiểm tra repository không kèm file runtime nhạy cảm: đạt trên các file hiện có.
- Không kiểm thử thật ứng dụng Windows/EXE; môi trường Linux hiện tại thiếu Flask/Werkzeug và không truy cập được kho gói để cài. Không thể coi các script BAT/EXE đã được kiểm nghiệm vận hành trên Windows.
- Chưa kiểm thử Chatwork/AI API thật, quyền thư mục Downloads trên máy đích hay mở Excel bằng ứng dụng Office/Excel trên Windows.

## Những điều cần nghiệm thu trên Windows trước khi phát hành cho nhân viên

1. `CAI_DAT_WINDOWS.bat` cài gói từ Internet thành công và kiểm tra mẫu 4 sheet đạt.
2. `CHAY_LOCAL_WINDOWS.bat` mở giao diện, đăng nhập/cấu hình API, đồng bộ dữ liệu giả, xuất chấm công.
3. Mở bản Excel bằng Microsoft Excel xác nhận không có cảnh báo `[Repaired]`.
4. Build EXE bằng `TAO_EXE_WINDOWS.bat`; chép EXE tới một máy Windows sạch, chạy, nhập lại khóa và kiểm tra Downloads.
5. Kiểm tra nhập dữ liệu và sao lưu/khôi phục SQLite nếu cần chuyển lịch sử giữa hai máy.

**Không nên cho nhiều máy sửa đồng thời chung một file SQLite qua thư mục mạng/OneDrive.** Nếu muốn dùng chung thời gian thực, triển khai hosting và Postgres riêng.
