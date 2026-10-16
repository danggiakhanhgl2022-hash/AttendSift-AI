# Kiểm chứng AttendSift AI 1.1.0 — 16/10/2026

## Đã thực hiện

| Kiểm tra | Kết quả |
|---|---|
| Toàn bộ pytest | 365 đạt, 0 lỗi, 0 bỏ qua |
| Kiểm thử UI tin nhắn bằng Node | Đạt |
| Trình duyệt Edge thật, Local và Cloud | Tab Nhân viên, thêm/nhập, tạo phiên, phân tích và chọn nhóm trong hộp rà soát đạt |
| Lỗi JavaScript trong hai luồng trình duyệt | Không ghi nhận |
| Build PyInstaller trên Windows x64 | Thành công |
| EXE kiểm tra thư viện và mẫu workbook | Đạt |
| EXE HTTP loopback | Trả phiên bản 1.1.0 |
| EXE với file khởi tạo riêng | Nhập đúng 27 người, trạng thái hoạt động |
| Dữ liệu nhân sự thật | Chỉ trong file riêng và gói nội bộ; không đưa vào kiểm thử công khai |

Các ca mới kiểm tra snapshot danh sách, ngừng hoạt động không bị nhập lại khôi phục, trùng tên/mã, danh sách trống cần xác nhận, CTV không cộng vào OT chính thức, giả mạo tên đầy đủ, nghỉ 1/0,5 ngày, nghỉ theo giờ không bị coi là nguyên ngày, nguồn dài được nối và chống công thức Excel.

API Cloud được kiểm thử qua Flask thật với repository giả lập và AI giả lập, không phải đo SQL trên Neon. Trình duyệt kiểm tra giao diện thực nhưng không gọi dịch vụ AI/Chatwork thật.

## Bằng chứng

Bộ bàn giao kỹ thuật có JUnit XML, kết quả trình duyệt, báo cáo runtime và checksum. Ảnh minh họa UI dùng người giả lập. Manifest ghi đúng hash EXE đã thử; commit build là commit cục bộ cho đến khi xuất bản từ GitHub.

Môi trường build dùng virtualenv có system-site-packages. Chưa coi đây là phép chứng minh cài sạch mọi dependencies hoặc quét bảo mật độc lập.

## Cần nghiệm thu riêng

- Windows độc lập của người nhận, cửa sổ WebView2 và Task Scheduler.
- API thật, quota và phạm vi lịch sử được cấp quyền.
- Workbook mở bằng Microsoft Excel không báo sửa chữa.
- PostgreSQL staging, đồng thời nhiều yêu cầu và retention trên dữ liệu thử.
- Chính sách nhân sự, điều kiện sử dụng và phân phối của đơn vị.
- Hiệu năng ở quy mô lớn; chưa có đo lường để công bố mức tải.

EXE chưa ký số. Đây là bản ứng viên phát hành để nghiệm thu nội bộ. Nguồn tham khảo kiến trúc không chứng nhận chất lượng hoặc độ chính xác của ứng dụng.
