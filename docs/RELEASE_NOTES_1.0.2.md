# AttendSift AI 1.0.2 — Windows & Cloud

Bản ứng viên phát hành gộp luồng chấm công Chatwork, cải thiện hiển thị cloud và tài liệu bàn giao Windows.

## Thay đổi

- Làm mới danh sách sau đồng bộ, phản hồi số lượng và bộ lọc rõ hơn.
- Hiển thị giờ tin nhắn cloud theo GMT+7, ngày/tháng/năm, không ngắt chuỗi ngày giờ.
- Sửa xác thực cron khi hostname deployment thay đổi, vẫn yêu cầu secret hợp lệ.
- Dọn tin nhắn, lịch sử, phiên phân tích và Excel cloud cũ hơn 3 tháng; ngăn nhập lại tin hết hạn.
- Thống nhất hướng dẫn Local/Cloud, chuyển máy, nhập lại khóa và kiểm chứng.
- Sửa lỗi tạo tài liệu làm mất dấu tiếng Việt; lưu UTF-8 và kiểm tra nội dung sau đóng gói.

## Cài đặt và nâng cấp

Người mới: giải nén Windows ZIP, đọc hướng dẫn, chạy kiểm tra rồi mở ứng dụng. Người dùng Local hiện có: đóng ứng dụng, sao lưu dữ liệu và làm theo hướng dẫn chuyển máy. Không đưa dữ liệu vận hành vào mã nguồn công khai.

Cloud: tải báo cáo cần giữ trước khi triển khai; cron hợp lệ đầu tiên có thể xóa ngay dữ liệu quá hạn. Chính sách không áp dụng SQLite Local hoặc Excel đã tải về.

## Kiểm chứng

Xem [báo cáo](VERIFICATION_1.0.2.md) và manifest đúng artifact. EXE chưa ký số. Máy nhận, API thật, Microsoft Excel và SQL retention trên staging cần được nghiệm thu riêng.
