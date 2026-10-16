# Checklist phát hành 1.0.2

Bằng chứng: [báo cáo kiểm chứng](VERIFICATION_1.0.2.md). Bản này dùng nhãn release candidate.

- [x] README VI/EN phân biệt Windows Local và cloud.
- [x] Hướng dẫn bao gồm GMT+7, cron và thời hạn lưu cloud 3 tháng.
- [x] Có hướng dẫn chuyển dữ liệu và biên bản bàn giao.
- [x] Có kiểm thử nguồn và kiểm tra tệp runtime bị cấm.
- [x] Tài liệu tiếng Việt lưu UTF-8, có kiểm tra dấu và ký tự thay thế.
- [ ] Nghiệm thu EXE trên Windows độc lập không cài Python.
- [ ] Kiểm tra WebView2, Downloads, Task Scheduler trên máy đích.
- [ ] Xác nhận API thật bằng tài khoản được phép.
- [ ] Microsoft Excel mở workbook không sửa chữa.
- [ ] Thử retention trên PostgreSQL staging.
- [ ] Kiểm tra lịch sử repository và quyền tài sản trước khi public.
- [ ] Chủ sở hữu xác nhận điều kiện sử dụng và phân phối.
- [ ] Tạo tag GitHub, build từ đúng tag và xuất bản ZIP/checksum.

Không đánh dấu hoàn tất khi chưa có bằng chứng. Checksum không thay thế ký số hoặc kiểm tra bảo mật độc lập.
