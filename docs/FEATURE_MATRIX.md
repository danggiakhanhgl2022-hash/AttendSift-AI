# Ma trận tính năng — 1.0.2

| Tính năng | Local | Cloud | Bằng chứng / giới hạn |
|---|---|---|---|
| Đồng bộ và lưu Chatwork | SQLite | PostgreSQL | Test giả lập; API thật cần nghiệm thu |
| AI và đối chiếu nguồn | Có | Có | Chưa đo độ chính xác tổng quát |
| Một tin nhiều người, nhiều ngày | Có | Có | Có test nghiệp vụ |
| Rà soát trước xuất | Có | Có | Cần đối chiếu quy chế đơn vị |
| Excel 4 sheet | Có | Có | Test cấu trúc; Microsoft Excel cần nghiệm thu |
| Formatter GMT+7 trong bản sửa mới | Theo giao diện Local | Có | Test UI cloud và chuyển ngày |
| Nhập lịch sử, backup/restore | Có | Không phải luồng Local | Không tự chuyển dữ liệu giữa hai bản |
| Lịch đồng bộ | Task Scheduler | Vercel Cron | Kiểm tra cấu hình thực tế |
| Xóa sau 3 tháng | Chưa áp dụng | Có | Test cutoff/quyền; SQL staging chưa nghiệm thu |
| EXE portable | Có spec/build | Không áp dụng | Xem báo cáo; máy nhận cần nghiệm thu |

Không suy ra hạn mức miễn phí, số người dùng hoặc hiệu năng từ việc tính năng có trong mã.
