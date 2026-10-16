# 03. Excel là giao diện bàn giao, không chỉ là một file tải xuống

[Trước](02-AI_VA_BANG_CHUNG.md) · [Mục lục](README.md) · [Tiếp: Local/Cloud](04-WINDOWS_VA_CLOUD.md)

## Tình huống: người nhận bảng không phải người bấm xuất

Một báo cáo được gửi cho người khác thường mất ngữ cảnh hội thoại. Chỉ đưa tổng OT sẽ khiến người nhận không biết dòng nào đã xác nhận, đâu là CTV và vì sao có tên chưa rõ. Vì vậy workbook được chia theo cách đọc: tổng quan → chi tiết → nguồn, với chỗ riêng cho các dòng cần xem lại.

![Bảng tổng kết giả lập](../images/story/03-summary.png)

## Vì sao giữ đủ năm sheet?

| Sheet | Câu hỏi của người nhận | Trách nhiệm |
|---|---|---|
| Tin gốc | “Có tin nào nói như vậy?” | Giữ căn cứ và ngày liên quan |
| Chấm công | “Người này được ghi những sự kiện nào?” | Chi tiết đủ căn cứ của nhóm chính thức |
| Tổng kết | “Tổng cuối cùng được tạo ra từ đâu?” | Tổng theo người, tách các chỉ tiêu |
| Cần kiểm tra | “Còn điều gì chưa thể kết luận?” | Lý do, trạng thái, dấu vết xác nhận/loại |
| CTV | “Phần người ngoài danh sách đang được xử lý thế nào?” | Chi tiết và tổng riêng, không trộn chính thức |

Tin nguồn được ghi dạng text để tránh nội dung bắt đầu bằng ký tự công thức bị diễn giải như công thức Excel. Tin dài có thể nối ô/dòng để tránh mất nội dung; ảnh minh họa chỉ chọn cột và rút gọn phần nhìn thấy, không đại diện toàn bộ dữ liệu workbook.

## Xuất trước không có nghĩa tính trước

![Dòng chưa được tính](../images/story/04-review.png)

Dòng “Quân OT 30p” có hai ứng viên nên được giữ ở sheet 4. Người đọc có file để kiểm tra ngay, còn tổng chính thức chưa chứa 30 phút đó. Sau khi có căn cứ, người phụ trách mở lại phiên, sửa/xác nhận và xuất lại. Bản file đã gửi trước đó không tự cập nhật.

Luồng này khắc phục tình trạng một dòng chưa rõ làm chặn cả workbook, nhưng tạo trách nhiệm theo dõi các dòng chưa xử lý. Nhãn “chưa tính công”, nguồn đối chiếu và báo cáo theo phiên giúp giảm nguy cơ đọc nhầm bản tạm thành bản hoàn tất.

## Cột mới nên bổ sung ở đâu?

Phút nghỉ có lương được thêm sau các cột đã có: AB ở chi tiết, O ở tổng kết và L ở CTV. Cách thêm cuối bảng giảm ảnh hưởng tới vị trí cột cũ, nhưng không đảm bảo mọi file macro, công thức hoặc báo cáo ngoài dự án đều tương thích. Người vận hành cần thử với công cụ Excel/WPS thực tế.

Không đổi tên một file tin thô thành “bảng công”. Đầu ra tin thô một sheet phục vụ đối chiếu nguồn, không có vai trò tổng hợp OT của workbook năm sheet.

## Những thứ đánh đổi với sự quen thuộc

Excel thuận bàn giao và kiểm tra offline. Đổi lại, file rộng, bản sao dễ phân tán và người nhận có thể sửa ngoài hệ thống. Biện pháp trong mã gồm liên kết Source ID, bản lưu theo phiên, hash file và tách nhóm dữ liệu. Việc phân phối, quyền truy cập hoặc lưu bản chính ngoài ứng dụng vẫn thuộc quy trình đơn vị.

Không trình bày các lớp kiểm tra trong ứng dụng như một chứng nhận bảng lương. AttendSift AI không tự quyết định đơn giá, khoản trả hoặc quan hệ lao động.

## Góc nhìn tham khảo

[Diátaxis](https://diataxis.fr/) phân biệt tài liệu theo nhu cầu người đọc. Bài này áp dụng góc nhìn đó vào cách **giải thích** workbook: người cần tổng khác người cần chứng cứ, nên mỗi sheet có một câu hỏi. Đây là suy luận thiết kế của dự án, không phải một tiêu chuẩn Excel do Diátaxis đề ra.

Điểm giữ lại: **người nhận phải lần được tổng về dòng, rồi về nguồn**. Xem [đủ năm hình](../PRODUCT_TOUR.md#excel-năm-góc-nhìn-của-cùng-một-báo-cáo).
