# 01. Từ công việc của người phụ trách đến cấu trúc sản phẩm

[Mục lục loạt bài](README.md) · [Tiếp: AI và bằng chứng](02-AI_VA_BANG_CHUNG.md)

## Tình huống: cuối tháng có số, nhưng chưa có lời giải thích

Một báo cáo ghi “Minh Quân OT 2h”, một tin khác gửi hôm sau báo hộ cả nhóm, rồi một nhân viên xin về sớm 30 phút. Người phụ trách không chỉ cần tổng. Họ cần biết ngày nào thực sự được tính, ai là người làm và dòng nào chưa đủ căn cứ.

Vì vậy, thông tin được xếp theo công việc: **Đồng bộ → Nhân viên → Xuất công → Lịch sử**, còn Thiết lập phục vụ các kết nối và lịch chạy. Người dùng có thể đi lại giữa các tab; đây là hành trình giải thích, không phải trình tự bắt buộc mới.

![Hành trình thông tin](../images/story/journey.svg)

## Giữ ba câu hỏi ở phía trước

| Câu hỏi | Nơi trả lời | Quyết định thiết kế |
|---|---|---|
| “Đang lấy tin từ đâu?” | Tab Đồng bộ và sheet nguồn | Hiển thị phòng, thời gian, Source ID, mức đầy đủ |
| “Vì sao tên này được tính?” | Danh sách theo phiên, chi tiết và sheet kiểm tra | Tách danh tính, căn cứ và trạng thái xác nhận |
| “Tôi sửa rồi có xem lại được không?” | Lịch sử phiên, ghi nhận sửa/xác nhận, báo cáo xuất lại | Giữ nguồn và các bước xử lý riêng với tổng |

Chi tiết kỹ thuật như SQLite, JSONB hoặc checkpoint có chỗ trong tài liệu bảo trì. Đưa chúng lên màn hình đầu tiên không giúp người phụ trách quyết định có thể dùng số liệu hay chưa.

## Lợi ích và chi phí của cách trình bày

Người đọc biết đầu ra trước khi phải hiểu công nghệ. Đổi lại, chia thành 5 tab và 5 sheet có thể tạo nhiều điểm chuyển qua lại. Biện pháp là gắn mỗi phần với một câu hỏi, cung cấp đường quay từ tổng kết về chi tiết và nguồn, đồng thời tách công cụ tải tin thô khỏi luồng xuất công.

Giao diện có cảnh 3D tạo nhận diện thị giác nhưng không giải quyết thiếu tin hay tên trùng. Giữ nó như lớp trình bày, cho phép tạm dừng và không dùng hình ảnh đó làm bằng chứng độ chính xác. Đây là đánh giá biên tập của dự án, không phải một thay đổi UI trong đợt tài liệu này.

## Ý tưởng tham khảo và cách chọn

Bài [Organizing productive platform teams](https://stackoverflow.blog/2026/03/09/organizing-productive-platform-teams/) của Adora Nwodo và Peter O'Connor, 09/03/2026, nhấn mạnh việc giảm gánh nặng phối hợp và tổ chức theo năng lực. Ở đây chỉ mượn góc nhìn giảm khó hiểu cho người dùng; không áp nguyên mô hình tổ chức đội platform vào một ứng dụng chấm công.

[C4 System Context](https://c4model.com/diagrams/system-context) giúp bắt đầu sơ đồ bằng con người và các hệ thống liên quan. Từ đó README đi từ người phụ trách, Chatwork, AI và Excel, rồi mới đến ranh giới mô-đun.

## Cách kiểm tra giá trị thay vì tự đánh giá “chuyên nghiệp”

Cho một người chưa biết dự án đọc README rồi yêu cầu họ chỉ ra cách xuất bảng, nơi xem dòng chưa rõ và giới hạn dữ liệu. Ghi thời gian tìm được câu trả lời, số lần phải hỏi và lỗi hiểu nhầm. Đây là đề xuất đánh giá tài liệu, **chưa có kết quả đo người dùng**. Việc trang đẹp hơn không tự chứng minh thao tác nhanh hơn.

Điểm giữ lại: **mỗi hình và mỗi mục phải giúp trả lời một câu hỏi cụ thể**.
