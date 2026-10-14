# Cài đặt và chuyển máy Windows (Local)

## Điều kiện

- Windows 10/11 64-bit, quyền cài Python/cài thư viện. Tốt nhất dùng **Python 3.11 x64**, bật Python Launcher.
- Truy cập Internet khi cài pip và khi sử dụng Chatwork/AI API.
- Thư mục có quyền ghi, ví dụ `C:\ChamCongChatwork`; tránh `Program Files` và thư mục chia sẻ/đồng bộ tài khoản.

## Từ mã nguồn

1. Vào trang repository GitHub > `Code` > `Download ZIP`; giải nén tại máy đích.
2. Cài Python 3.11 x64 nếu chưa có (theo python.org, chọn launcher/Add to PATH).
3. Nhấp đúp `CAI_DAT_WINDOWS.bat`; kiểm tra thông báo hoàn tất, không đóng khi đang cài.
4. Nhấp đúp `KIEM_TRA_LOCAL_WINDOWS.bat`; kiểm tra dependencies và mẫu workbook.
5. Nhấp đúp `CHAY_LOCAL_WINDOWS.bat`. Mở `http://127.0.0.1:8766` nếu trình duyệt không tự bật.
6. Trong Thiết lập, cấu hình Chatwork Room ID/API key và khóa AI chính chủ. Chỉ thử lần đầu bằng dữ liệu được phép xử lý.
7. Xuất bảng công 4 sheet, kiểm tra ở `Downloads`, mở bằng Excel/WPS và soát ít nhất 3 trường hợp OT nhóm.

### Build EXE trên Windows

Chạy `TAO_EXE_WINDOWS.bat` hoặc workflow Windows trong Actions; kiểm tra file phát hành dưới thư mục `release/`. Kiểm tra trên một máy Windows khác **không có Python** và xác nhận lịch sử, cấu hình khóa, bản Excel.

**Quan trọng:** file `ChamCong.exe` không có sẵn trong repository này. GitHub Actions được cấu hình, nhưng không có nghĩa là bản build đã được ký số hoặc chứng nhận sạch bởi Windows Defender.

## Chuyển dữ liệu từ máy cũ

- Mặc định: mỗi máy tự tạo một SQLite trống (`data/chamcong.db`).
- Muốn chuyển lịch sử: đóng hẳn app ở cả hai máy; sao lưu rồi copy riêng file `data/chamcong.db` sang cùng vị trí trên máy mới. Sao lưu trước khi ghi đè file hiện có.
- Có thể chuyển `outputs/sessions/` nếu có nhu cầu lưu các bản Excel cũ.
- **Không copy** file `*.credentials` từ tài khoản Windows cũ: DPAPI mã hóa theo tài khoản/máy và không dùng được ở nơi khác. Nhập lại khóa API trên máy mới.
- Không để nhiều máy ghi chung một file SQLite qua OneDrive/SMB vì dễ lỗi hoặc tranh chấp dữ liệu.

## Xử lý lỗi thường gặp

| Triệu chứng | Kiểm tra |
|---|---|
| `.bat` tắt nhanh | Chạy từ Command Prompt để đọc lỗi; xác nhận Python 3.11 và Internet |
| Port 8766 bị chiếm | Tắt cửa sổ/ứng dụng cũ đang mở cổng đó |
| Không thấy Excel trong Downloads | Kiểm tra thông báo đường dẫn của app và quyền ghi Downloads, thử đường dẫn chuyển vị trí |
| Không đọc được API key sau chuyển máy | Nhập lại khóa trên tài khoản Windows đích |
| Excel báo `[Repaired]` | Giữ file lỗi và kiểm tra bằng Microsoft Excel; không coi WPS mở được là đảm bảo |
| Thiếu các tin cũ | API có giới hạn lịch sử, nên đối chiếu dữ liệu gốc và nhật ký lần đồng bộ |

Tính năng Local không yêu cầu PostgreSQL. `cloud/` và `requirements-web.txt` là **tùy chọn khác**, không dùng trong các bước trên.
