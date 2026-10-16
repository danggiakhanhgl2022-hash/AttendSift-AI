# Một sản phẩm, năm tab, năm góc nhìn trong Excel

[Về README](../README.md) · [Đọc kiến trúc](ARCHITECTURE.md) · [Bài về Excel](articles/03-EXCEL_LA_GIAO_DIEN_BAN_GIAO.md)

Các ảnh giao diện bên dưới chụp từ ứng dụng Local trong trình duyệt Edge với database tạm và dữ liệu giả lập. Khi đóng gói Windows, giao diện này chạy trong WebView2. Đây là ảnh của sản phẩm hiện có, không phải bản thiết kế lại hoặc bằng chứng Cloud đã triển khai. Không có API thật được gọi trong quá trình tạo ảnh.

## 1. Đồng bộ: biết mình đang đọc nguồn nào

![Tab Đồng bộ](images/story/ui-sync.png)

Người dùng chọn phòng tại Thiết lập, xem trạng thái cập nhật và lọc tin đã lưu. Lịch sử nguồn được tích lũy qua các lần đồng bộ. Có nhiều tin không đồng nghĩa đã đủ cả tháng; nhãn nguồn và cảnh báo giúp người phụ trách quyết định có cần nhập thêm lịch sử.

## 2. Xuất công: bắt đầu từ kỳ cần làm

![Tab Xuất công](images/story/ui-export.png)

Tháng được chọn quyết định kỳ tính sự kiện. Tin từ ngày 15 tháng trước có thể làm ngữ cảnh, nhưng sự kiện ngoài tháng không được cộng vào tháng xuất. Luồng chính tạo workbook 5 sheet; công cụ tải tin thô được tách riêng để tránh nhầm đầu ra.

## 3. Lịch sử: quay lại quá trình tạo kết quả

![Tab Lịch sử](images/story/ui-history.png)

Phiên phân tích và hoạt động giúp trả lời ai đã được xử lý, khi nào và trạng thái nào được lưu. Mở lại phiên để đối chiếu, sửa hoặc xác nhận; xuất lại khi cần bản báo cáo đã cập nhật. File đã tải trước đó không tự thay đổi trên máy người nhận.

## 4. Thiết lập: cấu hình một lần, quản lý theo nơi chạy

![Tab Thiết lập](images/story/ui-settings.png)

Chatwork, nhà cung cấp AI và lịch đồng bộ có trách nhiệm riêng. Môi trường demo không chứa khóa sử dụng thật nên có trạng thái chưa kết nối. Khi chuyển máy hoặc chuyển giữa Local/Cloud, cần thiết lập theo nơi sử dụng; không sao chép khóa đã mã hóa của một tài khoản Windows sang tài khoản khác.

## 5. Nhân viên: danh sách là căn cứ phân loại

![Tab Nhân viên](images/story/ui-employees.png)

Thêm, sửa, ngừng hoạt động hoặc nhập danh sách riêng. Tên thường dùng cần được người quản trị xác nhận. Mỗi phiên giữ bản chụp danh sách; thay đổi danh sách hiện tại không tự sửa phiên cũ. Hai người cùng tên cần thêm tên đệm hoặc bằng chứng ID phù hợp.

## Excel: năm góc nhìn của cùng một báo cáo

Ảnh sau được dựng bằng công cụ tài liệu từ **giá trị workbook thật do mã nguồn xuất**, dùng các fixture giả lập. Một số cột được chọn để dễ đọc, nội dung dài có thể rút gọn trên ảnh; workbook và tin nguồn vẫn giữ nội dung theo cơ chế xuất. Đây không phải ảnh chụp hoặc biên bản nghiệm thu Excel/WPS.

### Sheet 1 — Tin nhắn gốc

![Tin nguồn](images/story/01-source.png)

Đọc Source ID, người gửi và ngày chấm công liên quan. Một người có thể báo hộ cả nhóm; ngày gửi cũng có thể sau ngày làm việc. Hai thông tin này không thay nhau.

### Sheet 2 — Chi tiết nhân viên chính thức

![Chi tiết chấm công](images/story/02-attendance.png)

Mỗi dòng là người/ngày/loại sự kiện, có Source ID. Nghỉ 30 phút có lương ghi ở cột riêng, không làm tăng phút thiếu giờ hoặc OT. Dòng chưa đủ căn cứ không có mặt trong phần được tính này.

### Sheet 3 — Tổng kết

![Tổng kết](images/story/03-summary.png)

Trong bộ demo có 180 phút OT chính thức và 60 phút nghỉ có lương. Đó là kết quả fixture, không phải số liệu nhân sự thực tế hoặc mức tiết kiệm thời gian. Có thể quay về sheet 2 và sheet 1 để giải thích các tổng.

### Sheet 4 — Cần kiểm tra

![Cần kiểm tra](images/story/04-review.png)

“Quân” khớp hai nhân viên chính thức nên chưa được cộng công. Sheet này cho thấy nguồn, vấn đề và trạng thái xử lý. Xác nhận bằng căn cứ phù hợp rồi xuất lại; không sửa tổng bằng cách đoán.

### Sheet 5 — CTV

![CTV](images/story/05-contractors.png)

Lan Demo có 45 phút OT CTV, được giữ riêng với nhóm chính thức. Phân loại ngoài danh sách phụ thuộc danh sách nhập đúng; thiếu nhân viên chính thức trong danh sách là việc cần quản trị dữ liệu, không phải bằng chứng người đó thật sự là CTV.

## Cảnh xe 3D có vai trò gì?

Đó là lựa chọn thị giác của giao diện hiện có. Nó tạo nhận diện nhưng chiếm không gian và tài nguyên hiển thị; người dùng có nút tạm dừng. Tài liệu không dùng chất lượng cảnh 3D để chứng minh tính đúng của chấm công. Hình minh họa nghiệp vụ và bảng đối chiếu mới là căn cứ để hiểu số liệu.
