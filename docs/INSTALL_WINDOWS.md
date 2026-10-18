# Cài và sử dụng Windows

## Bộ ZIP đầy đủ

Giải nén toàn bộ bộ bàn giao rồi mở `1_CHAY_UNG_DUNG/ChamCong.exe`. EXE không cần Python; máy cần Windows và WebView2.

Nhập danh sách chính thức tại Nhân viên. Cấu hình Chatwork và dịch vụ AI tại Thiết lập. Đồng bộ, chọn tháng, phân tích, đối chiếu các dòng cần kiểm tra rồi xuất Excel.

Tổng quan mặc định mở bảng Chính thức. Bảng lấy các sheet 2_CHAM_CONG/3_TONG_KET của Excel; CTV lấy 5_CTV. Nút Đọc file Excel chỉ đọc để hiển thị, không phân loại lại hoặc sửa file. Chọn đúng tháng và file; không dùng phiên khác để đối chiếu.

## Chạy và build mã nguồn

Cài Python 3.11. Chạy CAI_DAT_WINDOWS.bat rồi CHAY_LOCAL_WINDOWS.bat. Môi trường .venv nằm riêng trong dự án. Đóng EXE bằng build.bat; kết quả nằm ở BO_CAP_NHAT_5D/ChamCong.exe.

## Cập nhật hoặc chuyển máy

Đóng ứng dụng, sao lưu dữ liệu riêng rồi chỉ thay EXE trong thư mục chạy cũ. Không xóa database. Thư mục mới trống sẽ không tự có dữ liệu từ một thư mục chạy khác.

Gửi máy khác: gửi bộ chạy sạch. Bàn giao danh sách và dữ liệu thật riêng qua kênh nội bộ được phép, không qua GitHub.
