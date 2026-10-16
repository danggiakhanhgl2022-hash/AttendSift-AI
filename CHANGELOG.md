# Changelog

## Bổ sung ngày 16/10/2026

- Làm lại cấu trúc giới thiệu GitHub: hình mở đầu, ảnh 5 tab và 5 sheet bằng dữ liệu giả lập; thêm sáu bài phân tích cùng bảng nguồn, lựa chọn và đánh đổi.
- Bổ sung prompt biên tập, mục lục tài liệu và công cụ kiểm tra liên kết/hình minh họa; phân biệt rõ Local/WebView với Website Cloud.
- Giữ lại phần giới thiệu đầy đủ của phiên bản 1.1.0 và bổ sung hướng dẫn các quy tắc mới.
- Nghỉ 30 phút có lương: chỉ nhận tin tự báo có ngày, danh tính và nội dung đủ căn cứ; không trừ công, không cộng OT hoặc tự điền ngày trống.
- Đối chiếu tên với danh sách chính thức; giữ sự kiện thiếu bằng chứng riêng ở sheet kiểm tra.
- Cho phép sửa và xác nhận phiên đã xuất trên Local/Cloud; giữ số phút nghỉ có lương sau khi xác nhận.
- Kiểm tra lại dữ liệu ngay trước khi ghi Excel; dữ liệu không hợp lệ không được cộng vào tổng công.
- Giữ tương thích tên thường dùng do quản trị viên cấu hình cho các phiên cloud cũ.
- CI chạy toàn bộ kiểm thử, kiểm tra dữ liệu công khai và ngăn tải nhầm cache Python.

Kết quả kiểm tra hiện tại nằm tại [UPDATE_2026-10-16](docs/UPDATE_2026-10-16.md). Các mục bên dưới mô tả lịch sử tại thời điểm phát hành tương ứng; quy tắc ngày nghỉ đã được cập nhật ở trên và trong README.

## 1.1.0 — 2026-10-16 (release candidate)

- Tab Nhân viên: thêm, sửa, ngừng hoạt động và nhập danh sách riêng.
- Danh sách theo phiên; phân loại chính thức/CTV, giữ tên mơ hồ để kiểm tra.
- Workbook thêm 5_CTV, tách tổng OT và giữ tin nguồn.
- Xác định nghỉ nguyên ngày/nửa ngày theo từng ngày trong câu.
- Viết lại kiến trúc theo hành trình người dùng, có sơ đồ và bảng đánh đổi.


## 1.0.2 — 2026-10-15 (release candidate)

- Gộp sửa cloud: hiển thị tin nhắn, GMT+7, xác thực cron và dọn dữ liệu 3 tháng.
- Bổ sung hướng dẫn Local/Cloud, bàn giao máy mới, release notes và biên bản nghiệm thu.
- Chuẩn hóa tên AttendSift AI, phiên bản 1.0.2 và bằng chứng kiểm chứng.
- Gói Windows portable và ZIP nguồn chuẩn bị riêng; chưa ký số hoặc nghiệm thu máy độc lập.
- Sửa lỗi mất dấu tiếng Việt khi tạo tài liệu, thêm kiểm tra UTF-8 trước khi đóng gói.

## Lịch sử trước 1.0.2

Bản tài liệu ngày 14/10/2026 bổ sung README VI/EN, kiến trúc, nghiệp vụ, bảo mật, kiểm thử, demo và hướng dẫn sử dụng. Ảnh công khai đã che dữ liệu; không đưa video thô hoặc Excel nhân viên vào repository. Các báo cáo kiểm chứng có ngày riêng chỉ áp dụng lần chạy tương ứng.
