# Tự động dọn dữ liệu cloud sau 3 tháng

Cron `/api/cron/sync` dọn dữ liệu trước khi đồng bộ Chatwork. Chỉ yêu cầu có Bearer CRON_SECRET hợp lệ được chạy; không cần thêm cron hoặc chạy SQL thủ công.

| Dữ liệu | Cách tính hạn |
|---|---|
| Tin nhắn gốc | 3 tháng lịch từ thời điểm gửi |
| Phiên phân tích, bản chụp nguồn, kết quả và Excel của phiên | 3 tháng lịch từ thời điểm tạo phiên |
| Lịch sử thao tác | Bản ghi quá 3 tháng hoặc gắn với phiên bị xóa |
| Bản sửa tin nhắn | Bản sửa quá 3 tháng hoặc thuộc tin nhắn gốc bị dọn |

Cutoff tính theo giờ Việt Nam. Ví dụ 15/10 lúc 13:00 sẽ dọn dữ liệu trước 15/07 lúc 13:00. Ngày cuối tháng được điều chỉnh theo số ngày thực tế của tháng đích. Tin đúng cutoff được giữ.

Đồng bộ không nhập lại tin quá hạn. Phiên có lease xử lý còn hiệu lực được hoãn đến lần cron sau. Cấu hình, khóa API, thông tin phòng và tài khoản đăng nhập được giữ lại.

**Lần cron hợp lệ đầu tiên sau triển khai có thể xóa ngay dữ liệu đã quá hạn.** Hãy tải Excel cần giữ trước. Ứng dụng không tự sao lưu trước khi xóa. File đã tải về máy không bị tác động; chính sách này không áp dụng SQLite Local.

Phản hồi cron có `retention.cutoff` và `retention.deleted`. Lịch sử `retention` ghi số bản ghi đã dọn, không ghi nội dung nhân viên. Đồng bộ Chatwork lỗi sau bước dọn không khôi phục dữ liệu đã xóa. Nếu bước dọn lỗi, giao dịch dọn rollback.

Thời hạn lưu giúp kiểm soát tích lũy, không bảo đảm dữ liệu 3 tháng luôn vừa hạn mức miễn phí. PostgreSQL thường tái sử dụng chỗ trống; dung lượng hiển thị có thể không giảm ngay. Nghiệm thu SQL trên staging trước khi xác nhận vận hành ổn định.
