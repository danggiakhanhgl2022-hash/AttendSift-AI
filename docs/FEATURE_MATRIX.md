# Ma trận trạng thái tính năng

| Tính năng | Có trong mã | Có bài test | Xác nhận Windows thật |
|---|:---:|:---:|:---:|
| Giao diện Đồng bộ / Xuất công / Lịch sử / Thiết lập | Có | Một phần | Có ảnh/video người dùng; chưa nghiệm thu máy sạch |
| Lưu Chatwork → SQLite | Có | Có | Chưa kiểm tra API thật trong lần đánh giá này |
| AI phân tích và soát nguồn | Có | Có (mẫu mô phỏng) | Chưa đo độ chính xác tổng quát |
| Một tin nhiều người/multiple dates | Có | Có | Cần kiểm tra thêm dữ liệu thực theo kỳ |
| Phép năm / CTV chỉ lưu tin | Có | Có | Cần rà soát chính sách nơi sử dụng |
| Excel 4 sheet | Có | Có (cấu trúc) | Có ảnh WPS; Microsoft Excel cần nghiệm thu |
| Xuất Downloads | Có | Có (mock/path test) | Cần test khi Downloads bị đổi đường dẫn |
| Windows `.bat` cài/khởi chạy | Có | Static checks | Chưa thử hoàn chỉnh trên máy Windows mới |
| PyInstaller EXE | Có workflow/spec | Cấu hình tĩnh | **Chưa xác nhận EXE hoạt động** |
| Web hosting dùng chung | Có module cloud | Một phần | Ngoài phạm vi bản Local |

Không suy ra số lượng người dùng, thời gian xử lý hoặc độ chính xác AI khi chưa có đo lường/nhật ký kiểm định.
