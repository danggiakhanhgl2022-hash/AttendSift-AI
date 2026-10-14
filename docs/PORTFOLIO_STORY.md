# Development Story — giới thiệu năng lực kỹ thuật

## Bài toán

Trong một môi trường làm việc có báo cáo qua tin nhắn, dữ liệu chấm công không được nhập như một biểu mẫu chuẩn. Mỗi người có cách ghi khác nhau; tin nhóm có thể nêu ngày trước đó, nhiều người cùng một mức OT hoặc các mức khác nhau.

## Cách tiếp cận thể hiện trong dự án

1. **Tách thu thập và tính toán:** tin Chatwork được đồng bộ và lưu cục bộ trước khi sinh event.
2. **Truy vết:** một dòng kết quả liên kết tới tin gốc để người kiểm tra quay lại nguồn.
3. **Thiết kế nghiệp vụ:** biểu diễn theo nhân viên/ngày/loại; không chia OT nhóm; CTV và phép năm là hai quy tắc xử lý riêng.
4. **Quản lý độ không chắc chắn:** kết quả AI không tự động được coi là chính xác; có các bước đối chiếu và hàng chờ kiểm tra.
5. **Xuất báo cáo thân thiện quy trình:** Excel 4 sheet, tách dữ liệu nguồn và bảng chi tiết/tổng hợp.
6. **Local-first và chuyển máy:** SQLite trên Windows, `bat` thiết lập môi trường, cấu hình build EXE và GitHub Actions.

## Điều đã học / giới hạn kỹ thuật

- AI có thể nhầm ngày/nhân viên/OT; cần quy tắc kiểm chứng có khả năng kiểm thử.
- Công việc với thông tin chấm công nhạy cảm đòi hỏi traceability và quyền riêng tư.
- CI xanh không tương đương phần mềm đã được kiểm thử trong Excel Windows, WebView hoặc với API thật.
- Đóng gói cho người khác khác với chạy trên máy phát triển; cần hướng dẫn, bản build và quy trình nghiệm thu.

## Đoạn giới thiệu portfolio (dữ liệu dự án thực tế, không phóng đại)

**ChamCongChatwork** là một dự án Python Local-first trên Windows nhằm chuyển các báo cáo chấm công dạng hội thoại từ Chatwork thành sự kiện có cấu trúc. Dự án kết hợp đồng bộ dữ liệu, bộ phân tích AI, lớp đối chiếu nguồn và các quy tắc nghiệp vụ để xử lý tăng ca theo người/ngày, hỗ trợ bước rà soát trước khi xuất báo cáo Excel 4 sheet. Tôi tập trung vào khả năng truy vết, kiểm thử các trường hợp nhiều người/một tin, quản lý dữ liệu SQLite tại máy và chuẩn hóa quá trình cài đặt trên Windows. Đây là dự án đang trong giai đoạn release candidate; còn cần nghiệm thu runtime và kết nối API trên máy sạch.

**Tuyên bố đóng góp:** Nếu phát triển cùng người khác hoặc sử dụng công cụ AI, cần điều chỉnh cách viết ngôi "tôi" theo phần công việc bạn thực sự thực hiện. Không tuyên bố mọi dòng code được tự viết thủ công nếu không đúng.
