# Kiểm chứng bản 1.0.2 — 15/10/2026

## Kết quả thực đo trước bản sửa tài liệu UTF-8

| Kiểm tra | Kết quả |
|---|---|
| Pytest đầy đủ, dữ liệu giả | 326 đạt, 0 lỗi, 0 bỏ qua |
| UI cloud bằng Node | Đạt hiển thị, lọc, làm mới, GMT+7 và chuyển ngày |
| Chẩn đoán Local Windows | Python x64, thư viện, quyền ghi và template đạt |
| PyInstaller 6.22.3 / Python 3.11.9 / Windows x64 | Build EXE thành công |
| EXE --check-runtime | webview, requests, openpyxl và template đạt |
| EXE headless | Trang chủ HTTP 200, có form thiết lập |
| EXE /api/version | Trả 1.0.2 |
| Dừng tiến trình thử | Đã dừng |
| release_audit | Không có tệp runtime bị cấm |

Ba test kết nối cloud lỗi trước đây do thiếu cryptography. Môi trường virtualenv có thêm dependencies cloud giúp cả ba đạt, không sửa logic kết nối để né lỗi. Môi trường này dùng system-site-packages, không chứng minh cài sạch toàn bộ requirements.

## Sửa lỗi tiếng Việt

Lỗi đã xác định: truyền chuỗi Unicode qua pipe PowerShell sang Python làm mất ký tự trước khi ghi UTF-8. Việc đổi encoding khi mở lại không thể phục hồi dấu đã thành dấu hỏi. Tài liệu được viết lại bằng đường truyền ASCII/base64 chứa byte UTF-8, kèm công cụ kiểm tra nội dung tiếng Việt trong bản phát hành.

Gói nguồn, hướng dẫn trong ZIP Windows và checksum được tạo lại từ nội dung sửa. Không đổi logic xử lý trong EXE. Manifest ghi hash EXE và báo cáo runtime tương ứng; hash ZIP thay đổi khi tài liệu thay đổi.

## Chưa kiểm chứng

- Windows độc lập không cài Python, cửa sổ WebView2 và Task Scheduler trên máy nhận.
- API Chatwork/AI thật và độ chính xác tổng quát.
- Microsoft Excel mở workbook mới không sửa chữa.
- SQL retention trên PostgreSQL staging. Test cutoff và quyền cron không thay thế giao dịch xóa thật.
- Ký số, quét độc lập và toàn bộ lịch sử Git.

Dùng bản này để nghiệm thu nội bộ theo [biên bản bàn giao](HANDOVER_ACCEPTANCE.md). Không có việc diễn đàn chứng nhận sản phẩm.

## Kết quả sau sửa UTF-8

Toàn bộ 330 bài pytest đạt, 0 lỗi, 0 bỏ qua; kiểm thử UI Node đạt. Bộ kiểm tra xác nhận 16 tài liệu tiếng Việt còn nguyên dấu và không có ký tự thay thế lỗi. ZIP nguồn và hướng dẫn trong ZIP Windows được kiểm tra lại sau khi tạo; checksum được cập nhật theo đúng ZIP mới.
