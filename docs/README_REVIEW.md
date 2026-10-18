# Rà soát README — 17/10/2026

## Nguồn tham khảo và cách dùng

- [GitHub: About READMEs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes): trả lời sản phẩm làm gì, ai dùng, bắt đầu thế nào và nơi tìm trợ giúp.
- [GitHub Trending](https://github.com/trending): dùng để tìm ví dụ trình bày, không coi thứ hạng là chứng nhận chất lượng tài liệu.
- [OpenCode](https://github.com/anomalyco/opencode): dự án có trong trang Trending đã xem; phần mô tả ngắn và hướng dẫn cài đặt đặt gần đầu.
- [Ollama](https://github.com/ollama/ollama) và [Open WebUI](https://github.com/open-webui/open-webui): tham khảo tách khởi động nhanh khỏi tài liệu triển khai dài; đây là ví dụ trình bày, không tuyên bố đứng số 1/2.
- [Show HN guidelines](https://news.ycombinator.com/showhn.html) và [mục Show HN](https://news.ycombinator.com/show): ưu tiên thứ người đọc có thể xem/thử và trao đổi cụ thể. Đã xem [Flipflop](https://github.com/andunieee/flipflop) từ một bài Show HN, không dùng điểm bình chọn để chấm AttendSift.

Không có thang 9/10 chung được các diễn đàn công nhận. Điểm bên dưới là **rà soát biên tập nội bộ**, chỉ chấm README và bộ tài liệu bàn giao; không chấm độ chính xác AI, bảo mật tuyệt đối hay mức sẵn sàng triển khai sản xuất.

## Điểm trước và sau

README đang ở main khi kiểm tra tại commit 6ccd45c mô tả quy trình và căn cứ khá đầy đủ. Hạn chế: bìa minh họa thay vì giao diện mới; nhiều lối điều hướng sang báo cáo cũ; chưa phân biệt rõ phiên bản giao diện/lõi/Cloud; đường chạy bản đầy đủ và nguồn riêng chưa nhất quán với bộ bàn giao; chưa mô tả nguồn hiển thị Excel.

| Tiêu chí — mỗi mục tối đa 1 điểm | Trước | Sau | Bằng chứng bản mới |
| --- | ---: | ---: | --- |
| Nêu vấn đề và giá trị ngay đầu | 1 | 1 | Một câu về tin Chatwork, bảng công và đường đối chiếu |
| Tình huống sử dụng cụ thể | 1 | 1 | Bảng báo hộ, ngày gửi/ngày làm, tên nhập nhằng |
| Bắt đầu sử dụng được | 0,5 | 1 | EXE, lệnh Python và file BAT rõ ràng |
| Hình ảnh đúng sản phẩm | 0,5 | 1 | Ảnh/GIF chạy từ dữ liệu giả lập của phiên bản mới |
| Phạm vi và logic mô tả đúng | 0,5 | 1 | Bỏ chế độ 02; Local khác Cloud; không tự phân loại lại |
| Đầu ra và đường đối chiếu | 1 | 1 | Bảng 5 sheet, chỉ rõ nguồn bảng Chính thức/CTV |
| Kiểm chứng có phạm vi | 0,5 | 1 | 405 tests, lệnh chạy và giới hạn headless/API thật |
| Bảo vệ dữ liệu riêng | 1 | 1 | Không mang database, nhân viên, token vào Git |
| Hỗ trợ, lỗi thường gặp, vận hành | 0,5 | 0,5 | Có tài liệu và đóng góp; chưa có bộ FAQ nghiệm thu dài hạn |
| Cấp phép, thử nghiệm công khai độc lập | 0,5 | 0,5 | Nêu rõ quyền sử dụng chưa chốt; có minh họa nhưng chưa có sandbox công khai |
| **Tổng** | **7/10** | **9/10** | Điểm nội bộ, không phải chứng nhận bên ngoài |

Các kiểm tra tự động xác nhận liên kết/tài nguyên tồn tại, UTF-8, bố cục nguồn và dữ liệu bị cấm. Chúng không tự quyết định điểm thẩm mỹ. Không tăng điểm bằng badge “top”, số sao, hiệu năng hoặc độ chính xác chưa đo.

## Phần còn thiếu để đánh giá cao hơn

Chủ dự án cần quyết định giấy phép; nghiệm thu Windows/WebView và tài khoản được phép; bổ sung trải nghiệm thực tế và các lỗi thường gặp đã xử lý. README không gán nhãn MIT hoặc tuyên bố production-ready thay cho các việc đó.
