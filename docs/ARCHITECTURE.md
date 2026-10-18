# Kiến trúc

Windows Local dùng Flask, WebView2 hoặc trình duyệt loopback và SQLite. Cloud dùng ứng dụng riêng, PostgreSQL và biến môi trường hosting. Không tự đồng bộ database, danh sách nhân viên hay token giữa hai môi trường.

| Lớp | Trách nhiệm |
| --- | --- |
| Nguồn | Lưu tin Chatwork và phiên bản tin |
| Phiên | Snapshot nguồn, tháng và danh sách nhân viên |
| AI và quy tắc | Trích xuất rồi kiểm tra người, ngày, thời lượng và căn cứ |
| Xác nhận | Người phụ trách sửa, xác nhận hoặc loại, có lịch sử |
| Xuất | Workbook 5 sheet, tách chính thức/CTV/cần kiểm tra |
| Tổng quan | Chỉ hiển thị dữ liệu; bảng tổng đọc đúng sheet Excel |

Quy tắc phân loại vẫn thuộc nghiệp vụ ban đầu. Giao diện không khớp lại tên với danh sách hiện tại và không sửa phân loại của phiên cũ.

`src/app/workbook_view.py` chỉ đọc workbook có sẵn hoặc file được người dùng chọn. File chọn được đọc trong bộ nhớ, không lưu và không gửi tới AI. Sheet 3_TONG_KET cung cấp tổng chính thức; sheet 2_CHAM_CONG cung cấp số sự kiện; vùng TỔNG THEO NGƯỜI trong 5_CTV cung cấp tổng CTV. Không tính lại công thức khi workbook thiếu giá trị lưu; trả trạng thái chưa có giá trị.

`cinematic.js` dựng Neural Terminal. `reference-console.js` sắp xếp các vùng; `people-summary.js` hiển thị workbook. Chuyển động không đại diện suy nghĩ nội bộ của mô hình hay phần trăm tiến độ. Chế độ Operations Room đã được bỏ.
