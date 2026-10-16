# Nguồn tham khảo, cách chọn ý tưởng và đánh đổi

Đối chiếu ngày **16/10/2026** · [Kiến trúc](ARCHITECTURE.md) · [Loạt bài](articles/README.md)

## Tiêu chí thay cho một bảng xếp hạng không có căn cứ

Ưu tiên nguồn gốc có tác giả, bài mới phù hợp bối cảnh và tài liệu phương pháp chính thức. **InfoQ** và **Stack Overflow Blog** cung cấp các góc nhìn kỹ thuật có tác giả; **C4**, **Diátaxis** và **GitHub Docs** hỗ trợ cách tổ chức sơ đồ/tài liệu. Không có dữ liệu trong đợt này để khẳng định một trang là “top 1” hay “top 2” hiện tại. Nguồn không đánh giá hoặc chứng nhận AttendSift AI.

## Những bài đã đọc và cách áp dụng

| Nguồn gốc | Ngày xuất bản | Ý chính được chọn | Áp dụng vào tài liệu dự án |
|---|---|---|---|
| [Pierre Pureur & Kurt Bittner — You’ve Generated Your MVP Using AI…](https://www.infoq.com/articles/ai-generated-mvp/) | 12/02/2026 | Kiểm tra chất lượng và giả định bằng thử nghiệm, nói rõ đánh đổi | Mỗi tuyên bố có bằng chứng và phạm vi, tách kiểm thử giả lập khỏi nghiệm thu thật |
| [Adora Nwodo & Peter O'Connor — Organizing productive platform teams](https://stackoverflow.blog/2026/03/09/organizing-productive-platform-teams/) | 09/03/2026 | Giảm gánh nặng phối hợp, tổ chức theo năng lực | Mượn góc nhìn để trình bày theo câu hỏi của người phụ trách, không sao chép mô hình đội platform |
| [Pureur & Bittner — Three Questions That Help You Build a Better Software Architecture](https://www.infoq.com/articles/three-questions-better-architecture/) | 21/10/2025 | Giá trị, hiệu năng/quy mô và khả năng duy trì là các câu hỏi ưu tiên | Giải thích sản phẩm và tiêu chí trước khi kể tên công nghệ |
| [Pureur & Bittner — Software Architecture and the Art of Experimentation](https://www.infoq.com/articles/architecture-experimentation/) | 17/12/2024 | Dùng thử nghiệm để xem xét giả định | Ghi điều kiện thay đổi kiến trúc và phần chưa được đo |
| [Martin Fowler — Microservice Trade-Offs](https://martinfowler.com/articles/microservice-trade-offs.html) | 01/07/2015 | Lợi ích độc lập đi cùng chi phí phân tán/vận hành | Giữ cách đánh giá theo bối cảnh; chưa chọn tách microservices |
| [C4 — System Context](https://c4model.com/diagrams/system-context), [Container](https://c4model.com/diagrams/container) | Không gán ngày xuất bản; đọc 16/10/2026 | Đi từ người/hệ thống đến ứng dụng/kho dữ liệu | Tách sơ đồ ngữ cảnh khỏi sơ đồ hai môi trường |
| [Diátaxis](https://diataxis.fr/) | Không gán ngày xuất bản; đọc 16/10/2026 | Tổ chức theo nhu cầu học, làm, tra cứu và hiểu | README dẫn đường; hướng dẫn thao tác và bài giải thích có chỗ riêng |
| [GitHub Docs — About READMEs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes) | Tài liệu cập nhật liên tục; đọc 16/10/2026 | Giới thiệu dự án, bắt đầu sử dụng và tìm hỗ trợ | README có giá trị, ảnh, cách chạy, giới hạn và liên kết tài liệu |

Bài 2015/2024 được dùng cho lập luận nền, không làm bằng chứng xu hướng năm 2026. Bản tóm tắt là diễn giải ngắn; mở liên kết gốc để đọc ngữ cảnh và các lập luận phản biện đầy đủ.

## Từ nhiều ý tưởng đến một lựa chọn có lý do

| Ý tưởng | Quyết định | Lý do | Nhược điểm còn lại |
|---|---|---|---|
| Bắt đầu từ con người | Giữ | Người mới hiểu tác vụ trước cấu trúc mã | Cần liên kết đủ sâu cho người bảo trì |
| Sơ đồ nhiều cấp | Giữ vừa đủ | Ngữ cảnh và Local/Cloud có câu hỏi khác nhau | Phải cập nhật khi đổi ranh giới |
| Nhiều dịch vụ độc lập | Chưa chọn | Chưa có số liệu nhu cầu mở rộng/triển khai riêng | Một gói vẫn cần giữ mô-đun rõ |
| Toàn bộ kiểm tra giao cho AI | Không chọn | Gợi ý có thể thiếu nguồn hoặc sai người/ngày | Quy tắc xác định vẫn chưa hiểu mọi câu |
| Chặn toàn bộ Excel khi có một dòng mơ hồ | Không dùng trong quy tắc hiện tại | Người dùng cần file để đối chiếu trước | Cần nhãn rõ và theo dõi sheet chưa tính công |
| Đưa mọi tài liệu vào README | Không chọn | Trang đầu cần có nhịp đọc và điểm nhấn | Phải kiểm tra liên kết và hướng dẫn đọc tiếp |
| Ảnh đẹp làm bằng chứng sản phẩm đúng | Không chọn | Ảnh chỉ chứng minh phần nhìn thấy | Cần kiểm thử và nghiệm thu riêng |

Những quyết định này là phân tích của dự án, không phải các bài tham khảo cùng khuyên một giải pháp cụ thể cho AttendSift AI.

## Cân bằng ưu và nhược thế nào?

Mỗi lựa chọn được ghi theo bốn phần: lợi ích, chi phí, biện pháp giảm và điều kiện xem xét lại. Ví dụ snapshot giúp giải thích phiên cũ nhưng tăng dung lượng; retention giảm dữ liệu lưu nhưng tạo trách nhiệm tải báo cáo dài hạn. Không coi một ưu điểm tự triệt tiêu nhược điểm khác, và không cắt quyền riêng tư để đổi lấy cách trình bày ấn tượng.

Xem [bảng đánh đổi chi tiết](articles/05-LUA_CHON_VA_DANH_DOI.md). Các đề xuất hàng đợi, bảng nhân viên quan hệ hoặc dịch vụ độc lập là hướng tương lai, chưa được mô tả như khả năng đã có.

## Điểm nhấn được giữ trong phần giới thiệu

**Truy nguồn → đối chiếu theo phiên → tách dòng chưa rõ → bàn giao được.** Đây là chuỗi giá trị có liên kết tới mã và kiểm thử. Số công nghệ, cảnh 3D và số bài viết chỉ hỗ trợ cách giới thiệu; không được dùng thay độ đúng hoặc lợi ích đã đo.
