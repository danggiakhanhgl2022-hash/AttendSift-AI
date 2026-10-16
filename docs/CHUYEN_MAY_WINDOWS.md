# ChamCongChatwork 1.1.0 — chạy trên máy Windows khác

**Bộ phận AI · Đặng Gia Khánh**

## 1. Chọn cách dùng

| Cách dùng | Mở ở đâu | Dữ liệu nằm ở đâu | Cần cài Python? |
|---|---|---|---|
| Windows độc lập | `BAT_DAU.bat` hoặc `UngDung/ChamCong.exe` | Thư mục ứng dụng trên máy mới | Không |
| Website đã triển khai | `MO_BAN_WEB.url` | Neon, qua website | Không |
| Mã nguồn dành cho kỹ thuật | `MaNguon/ChamCongChatwork` | Tùy bản local hoặc cloud | Có |

Hai bản Windows và website không tự đồng bộ database với nhau. API đã lưu trên website không tự chuyển vào bản Windows.

## 2. Chạy ngay bản Windows

1. Chép ZIP sang Windows 10/11 **64 bit**.
2. Bấm chuột phải ZIP → **Extract All / Giải nén tất cả**. Không chạy trực tiếp bên trong ZIP.
3. Đặt thư mục đã giải nén ở nơi tài khoản có quyền ghi, ví dụ `D:\AttendSift-AI` hoặc thư mục Documents. Giữ thư mục này ổn định nếu dùng lịch tự động.
4. Mở `BAT_DAU.bat` hoặc `UngDung/ChamCong.exe`. Python và thư viện cần thiết đã nằm trong EXE; không chạy các lệnh pip.
5. Lần đầu có thể cần chờ EXE giải nén tài nguyên. Nếu WebView2 không khả dụng, ứng dụng sẽ thử mở trình duyệt mặc định tại `http://127.0.0.1:8766`.

Windows quản lý/chặn ứng dụng theo chính sách của từng máy. Nếu bị chặn, gửi tên tệp và mã SHA256 trong `THONG_TIN_GOI.json` cho bộ phận IT; không tắt phần mềm bảo vệ. EXE chưa ký số.

## 3. Thiết lập lần đầu

1. **Thiết lập → Bước 1:** nhập API token Chatwork → **Kiểm tra và lưu kết nối** → chọn nhóm → **Lưu nhóm đã chọn**.
2. **Bước 2:** chọn Google Gemini, OpenAI hoặc Claude → nhập API key → chọn model được tài khoản hỗ trợ nếu cần → **Kiểm tra và lưu kết nối**.
3. **Đồng bộ:** bấm **Đồng bộ ngay**, kiểm tra tin nhắn đã lưu. API thường chỉ trả cửa sổ tối đa 100 tin gần nhất; không coi đó là đầy đủ lịch sử.
4. **Xuất công:** chọn tháng → tạo bảng → kiểm tra/xác nhận các dòng cần rà soát → xuất Excel 5 sheet. File nằm trong Downloads của tài khoản Windows, có thể mở bằng Excel hoặc phần mềm tương thích XLSX.
5. Nếu cần tin cũ, vào **Thiết lập → Nhập tin nhắn lịch sử đã lưu**. Chỉ nhập dữ liệu được phép sử dụng; không nhập workflow n8n.

Internet cần cho Chatwork và dịch vụ AI. Giao diện và dữ liệu đã lưu nằm trên máy; gói EXE không bao gồm tài khoản hoặc quota API.

## 4. Chuyển dữ liệu từ máy cũ (tùy chọn)

1. Trên máy cũ: **Thiết lập → Sao lưu và khôi phục dữ liệu → Tạo bản sao lưu**.
2. Đóng ứng dụng trên cả hai máy. Chép tệp `backup_*.db` cần dùng vào `UngDung/backups` trên máy mới. Chỉ chuyển cho người có quyền xem dữ liệu nhân viên.
3. Mở ứng dụng máy mới → cùng mục sao lưu → xem bản sao lưu → khôi phục bản vừa chép. Hãy sao lưu dữ liệu đang có trên máy mới trước khi khôi phục.
4. Nhập lại API Chatwork và AI trên máy mới. Không chép `.credentials`: khóa local gắn với tài khoản Windows bằng DPAPI.
5. Nếu dùng đồng bộ tự động: **Lưu lịch** lại trên máy mới. Task Scheduler không được chuyển bằng cách chép thư mục.

Gói phát hành sạch không chứa dữ liệu nhân viên, API key, mật khẩu, database, log hay Excel thật từ máy đóng gói.

## 5. Lịch tự động và di chuyển thư mục

Bản Windows cần máy đang bật và tài khoản Windows đã đăng nhập để chạy lịch. Bản cloud chạy theo Vercel Cron, độc lập với máy cá nhân. Không chạy đồng thời cả hai lịch cho cùng một quy trình nếu chưa xác định cách đối chiếu dữ liệu.

Nếu đổi chỗ thư mục EXE, vào Thiết lập và **Lưu lịch** lại để cập nhật đường dẫn. Khi đổi máy, nhập lại khóa API.

## 6. Kiểm tra và hỗ trợ

- Chạy `KIEM_TRA.bat`: tạo `KIEM_TRA_MOI_TRUONG.json` kiểm tra thư viện và mẫu Excel của EXE.
- Nếu ứng dụng không mở: giải nén đầy đủ, kiểm tra quyền ghi thư mục và xem `UngDung/logs/application.log`.
- Nếu cổng 8766 đã được dùng: đóng bản đang chạy hoặc dùng `CHAY_CONG_KHAC.bat` để mở cổng 8767. Một thời điểm chỉ chạy một phiên trên cùng thư mục dữ liệu.
- Giao diện trắng hoặc không có cửa sổ: thử trình duyệt tại địa chỉ local khi EXE vẫn đang chạy; nhờ IT kiểm tra Microsoft Edge WebView2 Runtime nếu cần cửa sổ riêng.
- Lỗi API: kiểm tra token, model, quota và kết nối Internet. Không gửi key hoặc tin nhắn nhân viên trong ảnh báo lỗi.

Để gỡ bản portable, đóng ứng dụng và gỡ lịch đã tạo trong Task Scheduler nếu có; giữ bản sao lưu cần thiết trước khi xóa thư mục.

## 7. Nghiệm thu và dữ liệu cloud

Dùng [biên bản bàn giao](HANDOVER_ACCEPTANCE.md) để kiểm tra trên máy nhận. Chính sách xóa 3 tháng chỉ áp dụng website cloud; không xóa SQLite Local hoặc Excel đã tải về. Xem [vận hành cloud](CLOUD_OPERATIONS.md).
