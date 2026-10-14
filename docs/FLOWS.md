# User flow, System flow và Data flow — 1.0.0-rc11

## User flow

Mở EXE → Thiết lập Chatwork/phòng và AI mặc định → lưu lịch 13:00 hoặc giờ chọn → Đồng bộ → chọn tháng → kiểm tra dữ liệu → tạo phiên → kiểm tra dòng chưa rõ → xuất/tải Excel. Lịch sử cho mở lại phiên và tải đúng bản đã xuất. Có đúng bốn menu; không có menu Nhân viên hoặc Cần kiểm tra riêng.

Nếu thiếu dữ liệu cũ: Thiết lập → nhập MessageLog hoặc sheet tin gốc → kiểm tra số tin/mốc ngày → Xuất chấm công. Nhập lịch sử không gọi API hoặc AI, không ghi đè tin hiện có. Xuất tin riêng đọc database, không cần AI.

## System flow

Đồng bộ thủ công/lịch/chạy bù → kiểm tra cấu hình → khóa → Chatwork cửa sổ gần nhất → normalize → so mã/hash → transaction → phiên bản tin cũ khi sửa → lịch sử → mốc thành công. Lỗi không nâng mốc thành công. API cửa sổ 100 không có nghĩa database chỉ giữ 100.

Nhập lịch sử → đọc file → kiểm tra toàn bộ dòng → khóa/transaction → thêm mã chưa có → commit → lịch sử nhập. File workflow không được thực thi. Sheet kết quả chấm công không trở thành đầu vào AI.

Tạo bảng → kiểm tra chạy bù → đánh giá dữ liệu kỳ 15 tháng trước đến cuối tháng → xác nhận bản tạm → snapshot/phiên/cấu hình AI → các lô có giới hạn kích thước và registry nhận diện → JSON → validate local → review/corrections → kiểm tra nguồn chưa đổi → Excel pending → verify/hash → xuất atomic → trạng thái/history. Không được xuất bỏ qua lỗi bắt buộc.

## Data flow

Chatwork hoặc MessageLog lịch sử → SQLite messages/message_versions → snapshot bất biến → provider adapter → ai_results (raw và payload riêng) → corrections → bốn sheet Excel → Downloads theo tháng và outputs/sessions theo phiên → lịch sử liên kết phiên.

Key đi qua DPAPI ngoài SQLite; không có trong backup/ZIP/log. Backup dùng SQLite backup API và kiểm tra integrity/schema trước restore. Lịch Windows và recovery dùng cùng cấu hình giờ Việt Nam. Không dùng Employees/TeamDirectory làm điều kiện phân tích.

Xuất tin riêng: SQLite → lọc thời gian (15 ngày cuối tháng trước) → bản nội dung làm sạch → XLSX năm/tháng; không thay nguồn.

## Tự động local RC4
Một tác vụ Windows có CalendarTrigger theo giờ đã lưu và LogonTrigger trễ 30 giây. StartWhenAvailable chạy bù lịch bỏ lỡ; RestartOnFailure thử lại 10 phút/144 lần. --sync không mở web và không gọi AI. Khi bận hoặc lỗi trả mã 1; thành công/skipped trả 0.
Sang ngày mới có dữ liệu cũ: lấy bù một lần, giữ lịch hôm nay. Tất cả cập nhật mốc/slot chỉ sau commit. Background không chạy nếu lịch chưa được bật. Giờ mới đã qua hôm nay có effective_from ngày mai, không kích hoạt sớm.
