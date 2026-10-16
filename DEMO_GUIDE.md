# Demo dự án có thể chia sẻ công khai

## Bộ hình hiện tại — 16/10/2026

Xem [Product Tour](PRODUCT_TOUR.md) để dùng đủ **5 tab và 5 sheet** từ dữ liệu giả lập. Ảnh UI chụp thật ứng dụng Local; ảnh workbook được dựng từ giá trị xuất và ghi nhãn rõ, không trình bày như ảnh WPS/Excel. [Nguồn ảnh và tái tạo](images/story/README.md).

Các mục ảnh cũ bên dưới được giữ để ghi nguồn lịch sử. Kịch bản demo hiện tại: Đồng bộ → Nhân viên → Xuất công → tổng kết → dòng cần kiểm tra → CTV → lịch sử. Chỉ dùng người, phòng và tin giả lập; không quay khóa hoặc dữ liệu vận hành thật.

## Ảnh thực đã nhận và cách sử dụng

| Tệp ảnh | Nội dung thể hiện | Phần đã ẩn |
|---|---|---|
| `01-local-interface-redacted.png` | Tab Đồng bộ, giờ chạy và khu vực demo UI | Chatwork room và chi tiết cập nhật |
| `02-source-sheet-redacted.png` | Sheet `1_TIN_NHAN_GOC`, header/bộ lọc | Tên người gửi, mã tin, toàn bộ body |
| `03-attendance-sheet-redacted.png` | Sheet `2_CHAM_CONG` và các cột | Dữ liệu chi tiết nhân viên và OT |
| `04-summary-sheet-redacted.png` | Sheet `3_TONG_KET` | Dữ liệu tổng hợp theo nhân viên |

Ảnh **có thể chứng minh bố cục/giao diện**, không chứng minh kết quả số liệu vì dữ liệu đã che. Ảnh `4_CAN_KIEM_TRA` chưa được cung cấp ở bộ hình này, nên không dựng ảnh giả rồi ghi là ảnh chụp thật.

**Video gốc:** clip do người dùng gửi cho thấy thao tác chuyển tab, nhưng được ghi bằng camera và có thể lộ room/dữ liệu vận hành. Không đưa clip gốc lên GitHub Public.

## Kịch bản video demo 60–90 giây (ghi mới bằng dữ liệu giả)

1. Mở app tại `127.0.0.1`, giới thiệu năm tab và phân biệt Local với Cloud.
2. Dùng một room demo giả hoặc fixture không phải Chatwork nội bộ; hiển thị một tin có 2 ngày và nhiều người.
3. Tạo phiên chấm công, chỉ ra **6 dòng OT độc lập** từ một tin; chú thích nguồn.
4. Mở workbook 5 sheet; kiểm tra tổng chính thức, phút nghỉ có lương, dòng tên trùng và CTV riêng.
5. Mở thư mục Downloads chứng minh vị trí file.
6. Nêu giới hạn: mẫu demo, chưa xác nhận chính xác mọi tin tự nhiên và phụ thuộc cấu hình AI/API.

## Checklist trước khi bấm Record

Kiểm tra không hiện tên nhân viên thật, API token, số phòng, URL nội bộ, tên tài khoản Windows, lịch sử trình duyệt, file thật, thông báo app, ảnh/avatar nhạy cảm. Tắt popup notification. Nếu không thể đảm bảo, chỉ công bố ảnh đã che dữ liệu như gói này.
