# Development Story — giới thiệu năng lực kỹ thuật

## Bài toán

Trong một môi trường làm việc có báo cáo qua tin nhắn, dữ liệu chấm công không được nhập như một biểu mẫu chuẩn. Mỗi người có cách ghi khác nhau; tin nhóm có thể nêu ngày trước đó, nhiều người cùng một mức OT hoặc các mức khác nhau.

## Cách tiếp cận thể hiện trong dự án

1. **Tách thu thập và tính toán:** tin Chatwork được đồng bộ và lưu cục bộ trước khi sinh event.
2. **Truy vết:** một dòng kết quả liên kết tới tin gốc để người kiểm tra quay lại nguồn.
3. **Thiết kế nghiệp vụ:** biểu diễn theo nhân viên/ngày/loại; không chia OT nhóm; CTV và phép năm là hai quy tắc xử lý riêng.
4. **Quản lý độ không chắc chắn:** kết quả AI không tự động được coi là chính xác; có các bước đối chiếu và hàng chờ kiểm tra.
5. **Xuất báo cáo thân thiện quy trình:** Excel 5 sheet, tách nguồn, chính thức, tổng kết, kiểm tra và CTV; dòng chưa rõ chưa tính công.
6. **Local-first và chuyển máy:** SQLite trên Windows, `bat` thiết lập môi trường, cấu hình build EXE và GitHub Actions.

## Điều đã học / giới hạn kỹ thuật

- AI có thể nhầm ngày/nhân viên/OT; cần quy tắc kiểm chứng có khả năng kiểm thử.
- Công việc với thông tin chấm công nhạy cảm đòi hỏi traceability và quyền riêng tư.
- CI xanh không tương đương phần mềm đã được kiểm thử trong Excel Windows, WebView hoặc với API thật.
- Đóng gói cho người khác khác với chạy trên máy phát triển; cần hướng dẫn, bản build và quy trình nghiệm thu.

## Đoạn giới thiệu portfolio (dữ liệu dự án thực tế, không phóng đại)

**AttendSift AI** chuyển báo cáo Chatwork dạng hội thoại thành sự kiện có cấu trúc theo người/ngày. Dự án có Windows Local/SQLite và Website Cloud/PostgreSQL, dùng AI hỗ trợ đọc tin, đối chiếu nguồn và danh sách theo phiên, rồi xuất workbook 5 sheet. Điểm nhấn là truy vết kết quả, giữ riêng dòng chưa đủ căn cứ và tách CTV khỏi tổng chính thức. Bản cập nhật có quy tắc nghỉ 30 phút có lương và mở lại phiên đã xuất để xác nhận. 398 kiểm thử giả lập đã đạt ở môi trường ghi trong báo cáo; vẫn cần nghiệm thu API thật, Excel/WPS và máy Windows độc lập.

**Tuyên bố đóng góp:** Nếu phát triển cùng người khác hoặc sử dụng công cụ AI, cần điều chỉnh cách viết ngôi "tôi" theo phần công việc bạn thực sự thực hiện. Không tuyên bố mọi dòng code được tự viết thủ công nếu không đúng.

## Cách kể khi giới thiệu dự án

Bắt đầu bằng một tin báo hộ nhiều người, chỉ ra các sự kiện được tách, rồi lần từ tổng về Source ID. Giải thích tại sao một tên trùng nằm ở sheet kiểm tra và tại sao phần CTV không cộng vào chính thức. Kết thúc bằng lựa chọn Local/Cloud, một đánh đổi thực tế và bằng chứng kiểm thử. [Loạt bài](articles/README.md) cung cấp nội dung để đào sâu; không cần kể hết công nghệ ở phần mở đầu.
