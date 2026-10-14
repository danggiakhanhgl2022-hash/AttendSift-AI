# Biên bản đối chứng khi chuẩn hóa GitHub — 14/10/2026

## Bằng chứng đầu vào

- Gói mã nguồn: `ChamCongChatwork_GitHub_LOCAL_Windows_14-10-2026.zip` trong phiên xây dựng tài liệu.
- Ảnh giao diện Windows và 3 ảnh WPS (Tin nhắn gốc, Chấm công, Tổng kết) do chủ dự án cung cấp. Ảnh đưa vào repository đã được che opaque. Video gốc **không được đưa vào**.

## Các bước đã thực hiện trong môi trường Linux của ChatGPT

| Bước | Kết quả |
|---|---|
| Giải nén nguồn và đọc luồng Local/Excel | Thực hiện |
| Cú pháp Python `compileall` | Đạt |
| `tools/release_audit.py` để tìm file runtime cấm | Đạt ở trạng thái thư mục, kiểm tra gói ZIP riêng khi đóng gói |
| Nhóm 17 file test không phụ thuộc thư viện Windows đặc thù | **130 bài đạt / 130** |
| Nhóm test nghiệp vụ cốt lõi (5 file) | **51/51 đạt** (nằm trong 130 trên, không cộng số) |
| Chạy toàn bộ `pytest` trong Linux hiện có | **Không thành công khi collection**: thiếu `flask`/`werkzeug` |
| Chạy nhiều test phụ thuộc Windows DPAPI trong Linux | Không khả dụng; trả `SecretError` đúng rào chắn Windows |
| Build/chạy EXE trên máy Windows sạch | Chưa thực hiện |
| Kết nối Chatwork/AI API thật; mở file bằng Microsoft Excel | Chưa thực hiện |

**Chú ý:** Kết quả 130/130 là một *tập con được chọn*, không có nghĩa tất cả test trong repository đều đạt. Bộ test đủ môi trường cần chạy lại sau khi có Windows và dependencies.

## Tác động của ẩn danh fixture

Tên đầy đủ trong một số case kiểm thử được đổi sang dữ liệu giả, vẫn giữ cách ghép nickname/tên viết tắt. Hai bài test đối chiếu nickname ban đầu không còn tương ứng sau thay thế nên được điều chỉnh fixture để giữ được quan hệ nickname → full name, rồi chạy lại và đạt. Đổi fixture **không** thay đổi thuật toán nghiệp vụ chính.

## Kết luận trung thực

Đã chuẩn hóa tài liệu GitHub và các tệp cần thiết để trình bày dự án với bằng chứng giao diện thật nhưng ẩn dữ liệu. Đây là **kandidat kiểm thử**, chưa có biên bản chứng nhận hoạt động trên mọi Windows, chưa đánh giá độ chính xác AI, chưa hoàn tất rà quét bí mật bằng dịch vụ độc lập và chưa có lựa chọn giấy phép.
