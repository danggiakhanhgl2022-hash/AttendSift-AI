# Prompt biên tập phần giới thiệu GitHub

## Yêu cầu đã thống nhất

Viết lại phần mô tả GitHub cho **AttendSift AI**, dựa trên mã nguồn hiện có và các ảnh tham chiếu giao diện, Excel do chủ dự án cung cấp. Giữ phần thông tin hữu ích của bản giới thiệu ban đầu, mở rộng thành bộ tài liệu chuyên nghiệp, dễ đọc và có bằng chứng. Phạm vi gồm README, ảnh minh họa, kiến trúc và các bài phân tích; không thiết kế lại giao diện ứng dụng hoặc thay đổi quy tắc chấm công.

## Đối tượng và câu chuyện

Đặt người phụ trách chấm công ở trung tâm. Giải thích theo thứ tự: vấn đề khi đọc tin nhắn → kết quả nhận được → hành trình 5 tab → workbook 5 sheet → các quyết định kiến trúc → cài đặt → giới hạn và kiểm chứng. Phân biệt giao diện web chạy trong EXE Windows với website Cloud; không dùng ảnh WebView làm bằng chứng Cloud đã được triển khai.

## Điểm nhấn cần giữ

- Mỗi kết quả truy được Source ID và ngày sự kiện.
- Tách từng người, từng ngày, từng thời lượng trong báo cáo nhóm.
- Danh sách nhân viên được chụp theo phiên; tách chính thức và CTV.
- Nghỉ 30 phút có lương được ghi riêng theo tin báo có căn cứ, không tự trừ công hoặc thêm ngày trống.
- Dòng chưa xác minh nằm ở sheet kiểm tra và không cộng vào tổng công.
- Cả Windows/SQLite và Cloud/PostgreSQL có trong cùng gói mã nguồn.

## Kết quả cần bàn giao

1. README tiếng Việt có ảnh mở đầu, mục lục, ví dụ ngắn, sơ đồ dễ đọc, hướng dẫn bắt đầu, liên kết bài viết và bảng đánh đổi.
2. Bản tiếng Anh tương ứng; một câu GitHub About ngắn, rõ.
3. Bộ ảnh giao diện 5 tab và hình minh họa 5 sheet bằng dữ liệu giả lập; có chú thích nguồn ảnh và trạng thái mô phỏng.
4. Kiến trúc từ ngữ cảnh con người đến mô-đun, phân biệt thiết kế hiện có với hướng phát triển.
5. Loạt bài về quy trình, AI/đối chiếu, Excel, Local/Cloud, đánh đổi và bằng chứng kiểm thử; bài nào cũng có tình huống, lựa chọn, lợi ích, giới hạn và cách kiểm tra.
6. Bảng tổng hợp nguồn tham khảo, lý do chọn/không chọn ý tưởng và liên kết trực tiếp. Tham khảo bài có tác giả trên InfoQ, Stack Overflow Blog cùng C4, Diátaxis, GitHub Docs; không tự gán thứ hạng “top 1/top 2” khi không có dữ liệu xếp hạng.
7. Gói đầy đủ để cập nhật repository, gồm mã Windows/Cloud, ảnh và tài liệu; không kèm khóa, database hoặc dữ liệu nhân viên thật.

## Tiêu chuẩn kiểm tra trước khi bàn giao

- Mọi khả năng được giới thiệu phải đối chiếu được với mã nguồn hoặc báo cáo kiểm tra.
- Tài liệu hiện hành thống nhất 5 sheet; tài liệu lịch sử được ghi rõ mốc thời gian.
- Không biến kết quả 395 kiểm thử giả lập thành tuyên bố về độ chính xác API, tải thực tế hoặc nghiệm thu Microsoft Excel.
- Không đăng ảnh nhân viên, khách hàng, Source ID và tên phòng thật từ ảnh tham chiếu.
- Ảnh có giá trị giải thích; chữ đọc được, không dùng hình trang trí thay bằng chứng sản phẩm.
- Liên kết và ảnh nội bộ tồn tại, sơ đồ đúng ranh giới Local/Cloud, không có liên kết tải EXE giả.
- Ghi riêng: nguồn nói gì, dự án chọn gì và phần nào là đánh giá của tác giả.

## Kiểm tra prompt

Prompt này đã thu hẹp đúng yêu cầu được làm rõ: **sửa phần mô tả trên GitHub**. Ảnh giao diện là tham chiếu cho cách trình bày, không phải yêu cầu sửa UI. Hình minh họa sẽ được tạo từ dữ liệu giả lập; các quy tắc nghiệp vụ và giao diện hiện có được giữ. Không cần tạo website giới thiệu hay phát hành trên dịch vụ hosting mới.
