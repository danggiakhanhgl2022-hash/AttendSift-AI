# 05. Chọn điều nổi bật bằng cách ghi rõ phần phải trả

[Trước](04-WINDOWS_VA_CLOUD.md) · [Mục lục](README.md) · [Tiếp: kiểm chứng](06-KIEM_CHUNG_VA_GIOI_HAN.md)

## Tình huống: một dự án nhỏ dễ bị trình bày như một hệ thống rất lớn

Thêm tên công nghệ hoặc mô hình dịch vụ không tự tạo ra khả năng bảo trì. AttendSift AI cần giải thích đúng báo cáo, bàn giao được cho Windows và vận hành được trên Cloud. Thiết kế hiện có vì thế là ứng dụng chia mô-đun trong một gói triển khai cho mỗi chế độ; chưa phải kiến trúc có ranh giới được cưỡng chế hoàn toàn bằng công cụ.

## Bảng quyết định có điều kiện thay đổi

| Giữ lại hiện tại | Lợi ích | Giá phải trả | Biện pháp giảm | Khi cân nhắc đổi |
|---|---|---|---|---|
| Một gói chia mô-đun | Ít thành phần vận hành, dễ build EXE | Có thể gọi chéo và tăng coupling | Trách nhiệm rõ, kiểm thử dùng chung, rà soát thay đổi | Có nhu cầu triển khai/mở rộng độc lập được đo |
| Snapshot nguồn/danh sách theo phiên | Giải thích được bối cảnh báo cáo | Nhân bản dữ liệu và dung lượng | Retention, sao lưu, quản lý báo cáo | Đo được tăng trưởng vượt ngân sách lưu trữ |
| Danh sách có phiên bản trong settings | Phù hợp cấu trúc dữ liệu hiện tại | Cập nhật cả danh sách, hạn chế truy vấn lớn | Khóa thao tác, kiểm tra nhập, snapshot | Cần tìm kiếm/phân quyền/cập nhật đồng thời phức tạp |
| Xuất khi còn dòng cần rà soát | Có file để bàn giao, không chặn cả kỳ | Có thể quên dòng chưa được tính | Nhãn rõ ở sheet 4, mở lại phiên và xuất lại | Quy trình đơn vị đòi phê duyệt bắt buộc trước khi phát hành |
| Hai lớp lưu trữ | Phù hợp Local và Cloud | Hai đường điều phối có thể lệch | Test cả hai luồng với tình huống tương đương | Chi phí duy trì đủ lớn để thiết kế abstraction mới |
| Batching/checkpoint hiện có | Có thể tiếp tục khi tác vụ AI gián đoạn | Vẫn phụ thuộc giới hạn request hosting | Trạng thái rõ, thử lại có kiểm soát | Số liệu lỗi/thời gian cho thấy cần hàng đợi riêng |

Các điều kiện cuối bảng là hướng ra quyết định, chưa phải tính năng đã xây hoặc ngưỡng hiệu năng đã đo. Không cần mua thêm hạ tầng chỉ vì mô hình khác đang được nhắc nhiều.

## Tham khảo nhiều bài, giữ các ý tưởng bổ trợ nhau

[Martin Fowler: Microservice Trade-Offs](https://martinfowler.com/articles/microservice-trade-offs.html), 01/07/2015, phân tích lợi ích ranh giới/triển khai độc lập đi cùng chi phí phân tán và vận hành. Giữ ý tưởng so chi phí với bối cảnh, chưa chọn tách microservices cho dự án này.

[Pureur và Bittner: Three Questions That Help You Build a Better Software Architecture](https://www.infoq.com/articles/three-questions-better-architecture/), InfoQ 21/10/2025, đặt giá trị sản phẩm, hiệu năng/quy mô và khả năng duy trì thành các câu hỏi ưu tiên. Áp dụng: trước hết kiểm tra người dùng có đọc và đối chiếu đúng báo cáo, rồi mới đề xuất mở rộng kiến trúc.

[Software Architecture and the Art of Experimentation](https://www.infoq.com/articles/architecture-experimentation/), InfoQ 17/12/2024, dùng thử nghiệm để xem xét giả định kiến trúc. Áp dụng: mỗi quyết định quan trọng nên có tình huống và dấu hiệu thất bại đo được, thay vì chỉ sơ đồ đẹp.

Các bài cũ được giữ vì lập luận nền, không dùng để chứng minh xu hướng dẫn đầu năm 2026. [Bảng nguồn](../ARCHITECTURE_REVIEW_1.1.0.md) phân biệt thời điểm xuất bản và ngày đối chiếu.

## Ưu và nhược không tự triệt tiêu nhau

Snapshot giảm mất ngữ cảnh nhưng không sửa tin nguồn thiếu. Nhiều kiểm thử giảm lỗi đã biết nhưng không thay được nghiệm thu API thật. Excel dễ bàn giao nhưng vẫn có bản sao ngoài kiểm soát. Cách cân bằng là chỉ ra biện pháp, người chịu trách nhiệm và phần rủi ro còn lại, không dùng ưu điểm này che nhược điểm kia.

Điểm giữ lại: **quyết định có thể giải thích và có điều kiện xem xét lại**. Đó là điểm nhấn chuyên môn đáng trình bày hơn số lượng công nghệ.
