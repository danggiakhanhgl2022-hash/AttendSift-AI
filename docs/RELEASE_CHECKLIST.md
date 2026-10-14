# Pre-release checklist (RC)

> Chưa đạt Production Ready. Checklist bên dưới chỉ đánh dấu các bằng chứng đã có.

- [x] Có mã nguồn, README VI/EN, tài liệu kiến trúc, hướng dẫn Local.
- [x] Có `.gitignore`, không kèm SQLite/log/credentials trong gói đã rà soát.
- [x] Có screenshot đã che dữ liệu riêng tư.
- [x] Có script kiểm tra cấu trúc gói và tests chạy thử (xem verification).
- [ ] Nhận phản hồi trên Windows sạch từ ít nhất một máy độc lập.
- [ ] EXE chạy thành công và xuất Excel trên máy đích (có biên bản/ngày thử).
- [ ] `4_CAN_KIEM_TRA` được chụp an toàn, dữ liệu demo giả.
- [ ] Đối chiếu tình huống với Chatwork API thật trong môi trường đã được cấp phép.
- [ ] Quét toàn bộ commit history / secrets / dependency advisories trước khi public.
- [ ] Chọn giấy phép sử dụng; kiểm tra quyền tài sản bên thứ ba (ảnh, model 3D, thư viện).
- [ ] Tạo tag release và công bố checksum của artifact được kiểm tra.
