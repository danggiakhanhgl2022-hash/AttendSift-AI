# Bổ sung: nghỉ 30 phút có lương, không làm bù

Đây là **quy tắc nhận diện tin chấm công do công ty xác nhận**, không phải hồ sơ sức khỏe hoặc kết luận y tế của nhân viên.

## Nội dung nhận diện

Tin nhắn của **chính người xin phép** có lời báo rõ:

> Em xin phép về sớm 30 phút không làm bù. Em cảm ơn!

Khi có ngày, người gửi và câu báo phù hợp, chương trình ghi `Về sớm` với phân loại con
`Nghỉ 30 phút có lương - không làm bù`.

- `paid_break_minutes = 30` — số phút được hưởng lương.
- `minutes_not_compensated = 0` — **không** đưa 30 phút vào cột thiếu giờ/trừ công.
- `minutes_compensated = 0`; `ot_minutes = 0`; `leave_days = None`.
- Không tính thành lần về sớm thông thường trong tổng kết.
- Không tự suy đoán giới tính, lý do sức khỏe hay ghi chú y tế.

## Mỗi tin ứng với ngày thực tế

Nếu có tin ngày 12/10 và 14/10 mà không có tin ngày 13/10, hệ thống chỉ tạo **2 sự kiện**, tổng **60 phút nghỉ có lương**. Không yêu cầu đủ ba ngày, không tự tạo ngày nghỉ bị thiếu, không phụ thuộc lịch thứ Bảy/chủ nhật (chỉ những ngày có báo thực tế mới tính).

Tin `đi trễ 30 phút không làm bù` hoặc `về sớm 45 phút không làm bù` **không** áp dụng phân loại nghỉ có lương 30 phút này. Nếu tin thiếu thời gian hoặc từ khóa quyết định, hệ thống không tự cấp quyền nghỉ có lương.

## Giữ nguyên Excel 5 sheet

1. `1_TIN_NHAN_GOC`: giữ nguyên tin Chatwork.
2. `2_CHAM_CONG`: giữ nguyên các cột A:AA cũ; **thêm AB** “Nghỉ 30 phút có lương (phút)”.
3. `3_TONG_KET`: giữ nguyên các cột A:N cũ; **thêm O** “Tổng phút nghỉ có lương”.
4. `4_CAN_KIEM_TRA`: chỉ giữ các dòng có căn cứ chưa chắc chắn, không tính vào công.
5. `5_CTV`: giữ nguyên các cột A:K; **thêm L** thông tin nghỉ 30 phút có lương để dễ đối chiếu, không tự tính lương CTV.

Tên vẫn được trích đủ từ nguồn **trước** khi phân loại; dùng danh sách nhân viên chính thức và ID theo logic đang có. Không có thay đổi ở phần OT, nghỉ phép năm, xuất Excel trước–kiểm tra sau hay đồng bộ Chatwork.

## Lưu ý khi triển khai

Nên tạo **phiên phân tích mới** sau khi cập nhật để nạp quy tắc mới. Chỉ cập nhật ứng dụng Web không tự thay đổi EXE Local đã build; cần build lại EXE trên Windows. Các kết quả lương thực tế ở hệ thống ngoài AttendSift AI vẫn phải được đối chiếu với quy tắc này.
