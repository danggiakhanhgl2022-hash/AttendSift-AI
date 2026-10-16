# 06. Chứng minh điều đã làm, ghi riêng điều còn chưa biết

[Trước](05-LUA_CHON_VA_DANH_DOI.md) · [Mục lục](README.md) · [Kết quả kiểm tra](../UPDATE_2026-10-16.md)

## Tình huống: “395 tests passed” trả lời câu hỏi nào?

Lần kiểm tra Windows/Python 3.11.9 ngày 16/10/2026 có 395 kiểm thử Python đạt. Con số này cho biết các khẳng định trong bộ kiểm thử đã thỏa ở môi trường đó. Nó không cho biết AI hiểu đúng bao nhiêu phần trăm tin thực tế, bao nhiêu người dùng đồng thời hoặc tiết kiệm được bao nhiêu giờ.

## Mỗi tuyên bố cần một loại bằng chứng

| Tuyên bố | Bằng chứng đang có | Chưa suy ra được |
|---|---|---|
| Tách chính thức/CTV và tên trùng | Fixture nghiệp vụ, kiểm tra workbook | Danh sách nhân viên ngoài thực tế đã đầy đủ |
| Nghỉ có lương không trừ công | Test phút, cột, tổng và xác nhận sau xuất | Quy tắc phù hợp mọi đơn vị |
| Mở lại phiên đã xuất | HTTP/service regression ở Local/Cloud | Mọi thiết bị và mọi trình duyệt đã nghiệm thu |
| EXE có thư viện/mẫu workbook | Báo cáo `--check-runtime` đạt | Máy Windows sạch đã chạy WebView2 thành công |
| Hình README đúng sản phẩm | Capture từ app demo, workbook xuất từ fixture | Cloud đã triển khai hoặc ảnh là kết quả API thật |
| Gói nguồn không có dữ liệu chạy | Audit file cấm/mẫu secrets | Không còn mọi loại dữ liệu nhạy cảm có thể có |

## Điều đã sửa được kiểm tra thế nào?

Kiểm thử xuất lại xác nhận có thể sửa phiên sau khi tạo file, giữ số phút nghỉ có lương và kiểm tra lại dữ liệu ngay trước khi ghi. Các kiểm thử về dòng AI không hợp lệ được điều chỉnh theo quy tắc hiện tại: xuất được workbook, nhưng dòng lỗi chỉ ở sheet kiểm tra và tổng không bị ảnh hưởng.

Đây là thay đổi khẳng định kiểm thử để phản ánh đúng sản phẩm, không phải xóa bài kiểm thử bị đỏ hoặc thêm bỏ qua. Lỗi thiếu `cryptography` trong môi trường kiểm tra trước đã được phân biệt với lỗi ứng dụng bằng cách cài đúng dependency Cloud rồi chạy lại.

## Checklist trước khi dùng thật

| Nơi kiểm tra | Việc cần nghiệm thu |
|---|---|
| Chatwork | Quyền phòng, cửa sổ lịch sử, tin sửa, mức đầy đủ của kỳ |
| Dịch vụ AI | Kết nối thật, model được cấp quyền, chi phí, timeout và dữ liệu được phép gửi |
| Windows độc lập | WebView2, Downloads, quyền ghi, Task Scheduler và chuyển máy |
| Microsoft Excel/WPS | Mở không sửa chữa file, công thức/cache, bộ lọc, cột bổ sung và bản in |
| PostgreSQL staging | Khóa tác vụ, retention, lỗi mạng, phục hồi và giới hạn hosting |
| Người phụ trách | Hiểu sheet 4 chưa tính công, cập nhật danh sách và quản lý bản báo cáo |

Đợt tài liệu không thay biên bản nghiệm thu thật. Kiểm tra WebView tự động ở lần đóng gói trước chưa đạt; chụp được giao diện qua Edge không tương đương xác nhận WebView2 của EXE trên máy khác.

## Tham khảo và cách áp dụng

[Bài InfoQ về MVP tạo với AI, 12/02/2026](https://www.infoq.com/articles/ai-generated-mvp/) nhấn mạnh đánh giá chất lượng bằng thử nghiệm. Ở đây áp dụng bằng cách gắn tuyên bố với loại bằng chứng và giới hạn của nó. Đây là cách báo cáo của dự án, không phải bài tham khảo đã kiểm định phần mềm này.

Điểm giữ lại: **nêu được mình biết gì, nhờ phép thử nào, trong phạm vi nào**.
