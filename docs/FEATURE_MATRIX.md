# Ma trận tính năng — cập nhật 16/10/2026

| Tính năng | Local | Cloud | Bằng chứng / giới hạn |
|---|---|---|---|
| Đồng bộ và lưu Chatwork | SQLite | PostgreSQL | Test giả lập; API thật cần nghiệm thu |
| AI và đối chiếu nguồn | Có | Có | Chưa đo độ chính xác tổng quát |
| Một tin nhiều người, nhiều ngày | Có | Có | Có test nghiệp vụ |
| Xuất và rà soát theo phiên | Có | Có | Dòng chưa xác minh ở sheet 4; có thể mở lại phiên đã xuất |
| Excel 5 sheet có CTV | Có | Có | Phiên có danh sách; phiên cũ không có registry có thể giữ 4 sheet |
| Quản lý nhân viên và snapshot danh sách | Có | Có | Dữ liệu nhập riêng theo môi trường |
| Nghỉ 30 phút có lương | Có | Có | Chỉ theo tin tự báo đủ căn cứ; không tự trừ công/OT |
| Tên trùng, xung đột và dòng lỗi | Sheet kiểm tra | Sheet kiểm tra | Không cộng vào tổng chính thức hoặc CTV khi chưa hợp lệ |
| Formatter GMT+7 trong bản sửa mới | Theo giao diện Local | Có | Test UI cloud và chuyển ngày |
| Nhập lịch sử, backup/restore | Có | Không phải luồng Local | Không tự chuyển dữ liệu giữa hai bản |
| Lịch đồng bộ | Task Scheduler | Vercel Cron | Kiểm tra cấu hình thực tế |
| Xóa sau 3 tháng | Chưa áp dụng | Có | Test cutoff/quyền; SQL staging chưa nghiệm thu |
| EXE portable | Có spec/build | Không áp dụng | Xem báo cáo; máy nhận cần nghiệm thu |

Không suy ra hạn mức miễn phí, số người dùng hoặc hiệu năng từ việc tính năng có trong mã.

Xem [398 kiểm thử của bản sửa](UPDATE_2026-10-16.md), [bộ ảnh giả lập](PRODUCT_TOUR.md) và [so sánh môi trường](articles/04-WINDOWS_VA_CLOUD.md). Ảnh Local không chứng minh Cloud đã triển khai; các phép thử giả lập không thay nghiệm thu API hoặc Microsoft Excel/WPS.
