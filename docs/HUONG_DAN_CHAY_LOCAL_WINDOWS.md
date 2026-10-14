# Hướng dẫn chuyển sang Windows khác

| Thành phần | Trên máy mới | Có cần chuyển theo? |
|---|---|---|
| Mã nguồn trên GitHub | Tải ZIP và giải nén | Có |
| Python + pip packages | `CAI_DAT_WINDOWS.bat` | Có, nếu chạy từ nguồn |
| SQLite | Tự tạo trống khi khởi động | Không, nếu không cần lịch sử |
| `data/chamcong.db` | Chỉ chép `chamcong.db` khi app đã đóng | Chỉ khi cần lịch sử |
| `outputs/sessions/` | Lịch sử Excel | Chỉ khi cần giữ các file xuất trước đó |
| `data/*.credentials` | Khóa mã hóa Windows DPAPI | **Không**; phải nhập lại API key |
| Chatwork / AI keys | Nhập trong Thiết lập | Có, nhập bằng tay và giữ bí mật |
| Mẫu 4 sheet | Trong `templates/template.xlsx` | Kèm mã nguồn / EXE |
| `Cham_cong_MM_YYYY.xlsx` | Xuất tới Downloads mỗi máy | Tự tạo sau khi xuất |

## Kiểm tra tối thiểu trước khi giao cho người khác

1. Khởi chạy Local và mở trang chủ bằng browser.
2. Trong Thiết lập, lưu Chatwork API/AI API mới của máy thử nghiệm.
3. Đồng bộ tin giả lập hoặc nhập dữ liệu kiểm thử không chứa thông tin thật.
4. Tin 05/10 và 07/10 có 6 dòng OT: Thư 60, Tâm 120, Đăng 120; Thư 90, Tâm 30, Việt 60.
5. Tin nhóm 08/10: mỗi Đăng/Bảo/Quân/Việt 240 phút; không chia cho số người.
6. Các tin phép năm và My (CTV) chỉ giữ nội dung, không ghi vào tính công.
7. Xuất Excel sang Downloads, mở bằng Microsoft Excel hoặc WPS, xác minh đủ 4 sheet và không cảnh báo repair.

**Kiểm thử trên Windows thật với khóa API thật vẫn cần thực hiện.**
