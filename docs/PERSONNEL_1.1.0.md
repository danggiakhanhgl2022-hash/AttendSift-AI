# Nhân viên, CTV và ngày nghỉ — 1.1.0

## Chuẩn bị danh sách

Tab Nhân viên cho phép thêm, sửa, tìm kiếm và ngừng hoạt động. Mã nhân viên có thể trống; mã đã nhập, account ID và tên thường dùng không được trùng theo quy tắc kiểm tra.

Gói cài nội bộ có thể kèm NHAN_VIEN_RIENG.json bên cạnh EXE. Lần đầu hệ thống nhập danh sách nếu chưa được khởi tạo; những lần sau không ghi đè. Trên website, đăng nhập rồi vào Nhân viên → chọn file JSON → Nhập danh sách. File riêng không được tải lên cây mã nguồn GitHub.

Ngừng hoạt động giữ hồ sơ để liên kết báo cáo cũ. Có thể kích hoạt lại bằng thao tác rõ ràng; nhập lại danh sách không tự kích hoạt.

## Phân loại

- Khớp duy nhất với họ tên hoặc tên thường dùng đã xác nhận: chính thức.
- Nguồn ghi rõ CTV: CTV, trừ khi xung đột với danh sách chính thức.
- Danh tính rõ, không khớp và không có nghi ngờ là tên ngắn của người trong danh sách: CTV tự phân loại.
- Tên thiếu, có khả năng trùng hoặc xung đột: cần kiểm tra.

Không suy ra rằng mọi người được nhắc đều là người gửi. Một tin có hai nhóm sẽ tách từng người. Nhãn CTV là phân loại phục vụ báo cáo, không xác nhận pháp lý.

Trong hộp kiểm tra, chọn nhóm và nhân viên từ danh sách đã chụp của phiên. Có thể lưu tên nguồn làm tên thường dùng sau xác nhận; việc này áp dụng cho phiên mới. Nhân viên vừa thêm sau khi tạo phiên cần được dùng qua phiên mới.

## Ngày nghỉ

“Nghỉ ngày 05/10” = 1 ngày. “Nghỉ sáng 06/10” hoặc “nghỉ chiều 06/10” = 0,5 ngày. Hai buổi cùng ngày = 1 ngày. Tin có nhiều ngày được tách riêng.

“Em xin phép nghỉ ngày 05/10 và sáng ngày 06/10” tạo 1 + 0,5 = 1,5 ngày. Không bắt nhập giờ nếu đã rõ buổi. Nghỉ theo giờ chưa có quy tắc quy đổi vẫn cần kiểm tra.

Không suy diễn “xin phép nghỉ” thành “phép năm”. Quy tắc phép năm đã có vẫn giữ nguồn theo chính sách cũ. Cột ngày nghỉ mọi loại giúp thể hiện thời lượng mà không tự xác định tiền lương.

## Workbook

Phiên mới có năm sheet, trong đó 5_CTV chứa chi tiết, căn cứ, Source ID, nguyên văn và tổng OT/ngày nghỉ theo người. OT CTV không cộng vào tổng chính thức.

Nếu nội dung dài hơn giới hạn một ô, nguồn CTV được nối bằng các dòng tiếp theo; dòng nối có OT và ngày nghỉ bằng 0 để không cộng trùng. Phiên cũ giữ đầu ra cũ.

## Nâng cấp

Sao lưu trước nâng cấp. Dữ liệu danh sách dùng khóa settings có phiên bản; không cần thay cấu trúc bảng hiện có. Thêm trường snapshot trong JSON của phiên mới, không chuyển ngầm chính sách phiên cũ.

Chính sách dọn dữ liệu cloud không xóa danh sách nhân viên. Local và cloud không tự đồng bộ danh sách. Kiểm tra hai nơi nếu dùng cả hai.
