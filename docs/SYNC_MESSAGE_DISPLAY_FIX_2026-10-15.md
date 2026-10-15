# Khắc phục: Đồng bộ thành công nhưng không hiển thị tin nhắn (15/10/2026)

## Nguyên nhân được xác nhận từ mã nguồn và ảnh giao diện

1. Ở giao diện **Web/Cloud (Vercel)**, nút `Đồng bộ ngay` chỉ gọi `POST /api/sync`, cập nhật thông báo, **không gọi `GET /api/messages` để nạp lại danh sách**. Bởi vậy người dùng phải bấm thêm `Lọc tin nhắn`.
2. Trong HTML, `Đến ngày` hiển thị trước `Từ ngày`. Ảnh tình huống thể hiện **Đến ngày = 01/10/2026** và **Từ ngày = 15/10/2026**. Điều kiện lọc JavaScript `(day >= start && day <= end)` loại hết tin khi `start > end`, nhưng giao diện chỉ báo chung "Không có tin nhắn phù hợp".
3. Khi đổi tháng, bộ lọc ngày trước đó không được đặt lại, dễ khiến tháng mới không hiện dữ liệu.

`100 tin trong kỳ; 65 tin gửi trong tháng` là số liệu từ `GET /api/messages`, không phải số dòng đang hiển thị. API tính cả phần ngữ cảnh từ tháng trước để giúp trích sự kiện đúng tháng. Số liệu này chưa chứng minh toàn bộ lịch sử Chatwork đã được lấy đủ (giới hạn cửa sổ tin của Chatwork).

## Thay đổi đã thực hiện

- Gọi nạp lại danh sách ngay sau khi đồng bộ thành công, đồng thời tự tải tin đã lưu khi mở trang có cấu hình phòng hợp lệ.
- Đổi thứ tự ô nhập thành `Từ ngày → Đến ngày`.
- Cảnh báo rõ khi người dùng chọn khoảng ngày ngược và giữ nguyên cache; không âm thầm xóa dữ liệu.
- Cho biết số tin **đang hiển thị / đã tải** và giải thích khi bộ lọc không khớp.
- Khi đổi tháng, xóa bộ lọc **ngày** cũ, tải dữ liệu tháng đã chọn và bỏ qua phản hồi cũ đến muộn.
- Sau khi chọn phòng mới, tải lại danh sách thuộc phòng đó, tránh hiển thị nhầm cache phòng cũ.
- Sử dụng múi giờ `Asia/Ho_Chi_Minh` cho ngày gửi tin; dựng DOM bằng `textContent`, không nhúng HTML từ nội dung Chatwork.
- Cập nhật phiên bản URL script để hạn chế trình duyệt dùng cache mã cũ. Sửa **cả** `cloud/static/cloud.js` và `public/static/cloud.js` do Vercel có thể phục vụ assets từ `public/`.

**Không thay đổi**: đồng bộ Chatwork phía máy chủ, cấu trúc database, quy tắc phân tích OT, chính sách nghỉ phép, xuất Excel 4 sheet, bản Windows Local.

## Cách kiểm tra sau triển khai Web

1. Cập nhật mã nguồn trên GitHub và để Vercel deploy thành công; dùng `Ctrl+Shift+R` để tải trang mới.
2. Chọn nhóm Chatwork đúng; ở mục Đồng bộ, chọn tháng 10/2026.
3. Bấm **Đồng bộ ngay**: sau khi đồng bộ xong, các tin đã có trong kỳ sẽ tự hiện (không cần bấm nút lọc lần nữa).
4. Để trống cả hai ngày sẽ xem mọi tin trả về trong khoảng ngữ cảnh kỳ (bao gồm một phần tháng trước). Nếu chỉ cần tháng 10, nhập **Từ ngày 01/10/2026**, **Đến ngày 15/10/2026** (hoặc ngày cuối tháng).
5. Nếu cố ý đảo ngược hai ngày, giao diện phải báo "Khoảng ngày không hợp lệ" và giữ số tin đã tải; sửa hai ngày thì danh sách hiện lại.
6. Kiểm tra đồng thời `3_TONG_KET` / Excel không đổi so với bản cũ.

## Các bài kiểm thử thực hiện trong môi trường này

- `node tests/test_cloud_message_ui.cjs`: dựng DOM và API giả, kiểm tra 100 tin hiển thị, 65 tin tháng 10, ngày bị đảo ngược, tải lại sau đồng bộ, chuyển tháng và lọc từ khóa.
- `python -m pytest -q tests/test_cloud_message_display_contract.py`: kiểm tra đồng nhất asset, thứ tự ngày và liên kết cache-busting.
- `node --check cloud/static/cloud.js` và `node --check public/static/cloud.js`.

**Giới hạn**: Chưa kết nối vào PostgreSQL/Chatwork/Vercel thật; chưa thể xác nhận thông qua trình duyệt thực trên môi trường deploy. Không kết luận API trả đủ lịch sử chỉ từ con số 100 tin.

## An toàn dữ liệu

Gói người dùng gửi chứa thư mục phụ thuộc Windows, **database SQLite cục bộ**, lock và log. Chúng **không có trong ZIP trả lại** để tránh vô tình đưa tin nhân viên hoặc thông tin cấu hình lên GitHub. Mã cấu hình mẫu và dữ liệu kiểm thử giả được giữ lại.
