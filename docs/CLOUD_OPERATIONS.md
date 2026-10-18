# Vận hành website AttendSift AI 1.0.2

## Thành phần và cấu hình

Website dùng Flask trên Vercel và PostgreSQL trên Neon. Local Windows dùng SQLite riêng; hai bản không tự trao đổi dữ liệu.

Dùng `.env.example` và phần kiểm tra cấu hình trong `cloud/app.py` làm tham chiếu. Thiết lập DATABASE_URL, session secret, password hash quản trị, allowed hosts và CRON_SECRET qua biến môi trường hosting; không đưa giá trị thật vào repository. Retention dùng bảng đã có, không cần migration riêng. Cài mới database vẫn cần chạy `python -m cloud.migrate` trong môi trường đã cấu hình.

## Sau mỗi lần cập nhật

1. Kiểm tra deployment đúng commit và trạng thái Ready.
2. Đăng nhập website, kiểm tra phòng và nhà cung cấp AI.
3. Đồng bộ, đối chiếu số tin và bộ lọc. Thời gian hiển thị GMT+7.
4. Xem log `/api/cron/sync`; HTTP 200 chỉ xác nhận yêu cầu hoàn tất, vẫn cần kiểm tra kết quả nghiệp vụ.
5. Giữ `cloud/static/cloud.js` và `public/static/cloud.js` cùng nội dung; tải lại Ctrl+F5.

## Cron và retention

Lịch `0 6 * * *` trong vercel.json tương ứng mốc dự kiến 13:00 giờ Việt Nam mỗi ngày. Cấu hình lịch không cam kết thời điểm thực thi chính xác của hosting.

Endpoint yêu cầu Bearer CRON_SECRET tối thiểu 32 ký tự. Cron đã xác thực được ngoại lệ host khi deployment URL thay đổi. Không đưa token vào URL hoặc ảnh hỗ trợ.

## Sửa lỗi “Host không hợp lệ” trên Vercel

Khi `VERCEL=1`, ứng dụng tự thêm chính xác các hostname từ `VERCEL_URL`, `VERCEL_BRANCH_URL` và `VERCEL_PROJECT_PRODUCTION_URL` vào danh sách cho phép. Không tin `X-Forwarded-Host`, không mở toàn bộ `*.vercel.app`. Các biến này phải là hostname thuần, không có `https://`, cổng hoặc đường dẫn.

Với tên miền riêng, đặt `CHAMCONG_ALLOWED_HOSTS` thành danh sách hostname cách nhau bằng dấu phẩy, ví dụ `attend-sift-ai.vercel.app,attendance.example.com`. Khi chạy ngoài Vercel, biến này vẫn bắt buộc. Nếu Vercel chưa cung cấp biến hệ thống, bật **Automatically expose System Environment Variables** trong Project Settings rồi redeploy. Sau khi sửa biến môi trường phải tạo deployment mới.

Kiểm tra `/login` trên URL production và deployment mới: trả 200; `/` khi chưa đăng nhập chuyển tới `/login`; `/api/config` khi chưa đăng nhập trả 401. Host ngoài danh sách phải tiếp tục trả 403. Không cần thay session secret hoặc mật khẩu để sửa lỗi host.

Tham chiếu: [biến hệ thống Vercel](https://vercel.com/docs/environment-variables/system-environment-variables), [an toàn Host header trong Flask](https://flask.palletsprojects.com/en/stable/web-security/#host-header-validation).

Mỗi lần cron hợp lệ: dọn dữ liệu quá hạn trong một giao dịch PostgreSQL, ghi số lượng dọn, rồi đồng bộ Chatwork. Nếu đồng bộ sau đó lỗi, bước dọn đã hoàn tất. Nếu dọn lỗi, rollback giao dịch dọn và cron trả lỗi. Phiên đang có lease được hoãn tới lần sau.

Đọc [chính sách 3 tháng](RETENTION_3_MONTHS.md) trước khi triển khai. Ứng dụng không tự khôi phục dữ liệu đã xóa. Tải báo cáo cần giữ; chỉ dựa vào backup nhà cung cấp khi đã kiểm tra điều kiện tài khoản.

## Dung lượng và nghiệm thu

Theo dõi Storage và hạn mức thực tế trong console Neon/Vercel. Dữ liệu 3 tháng vẫn có thể vượt quota nếu lượng tin hoặc file lớn. PostgreSQL có thể tái sử dụng chỗ trống sau DELETE; dung lượng hiển thị không nhất thiết giảm ngay.

Trên PostgreSQL staging độc lập, tạo dữ liệu trước, đúng và sau cutoff; thử cron hợp lệ và không hợp lệ; đối chiếu file, phiên, message version và settings. Không dùng production để thử xóa.

Xác nhận API thật bằng tài khoản được phép và mở Excel bằng Microsoft Excel. Ghi ngày, phiên bản và kết quả trong biên bản bàn giao.
