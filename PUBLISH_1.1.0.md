# Cập nhật và bàn giao 1.1.0

## Mã nguồn công khai

Mở thư mục UPLOAD_GITHUB_1.1.0 bằng File Explorer, chọn nội dung bên trong rồi kéo vào trang upload ở gốc repository trên nhánh main. Không kéo thư mục bao ngoài. Mô tả commit: Add employee registry, contractor worksheet and human-centered architecture docs.

Không tải ZIP cài nội bộ, NHAN_VIEN_RIENG.json, database hoặc báo cáo nhân sự lên GitHub. ZIP nguồn công khai không có danh sách thật. Sau commit, kiểm tra Actions và Vercel deployment đúng phiên bản.

## Website

Sau khi deployment Ready, tải lại Ctrl+F5, đăng nhập → Nhân viên → chọn file NHAN_VIEN_RIENG.json riêng → Nhập danh sách. Kiểm tra tổng 27 người, bổ sung mã hoặc tên thường dùng khi cần. Tạo phiên mới để dùng chính sách mới; phiên cũ giữ kết quả cũ.

Dữ liệu danh sách dùng khóa employee_registry_v1 trong cc_settings. Không cần migration bảng riêng. Chỉ thử trên staging trước khi xác nhận PostgreSQL đã nghiệm thu.

## Windows

Gói nội bộ CAI_MAY_KHAC_1.1.0.zip có ChamCong.exe ở ngoài cùng, NHAN_VIEN_RIENG.json và hướng dẫn. Giải nén đầy đủ rồi mở EXE. Danh sách tự khởi tạo khi chưa có; không ghi đè danh sách đã chỉnh sửa.

Nâng cấp máy đang dùng: đóng app, sao lưu qua giao diện, giữ thư mục dữ liệu và khóa hiện có; thay EXE đã kiểm tra tại đúng thư mục. Lưu lại lịch nếu thay vị trí ứng dụng. Không tự chép credentials sang tài khoản Windows khác.

## Xuất bản release

Tạo pre-release từ commit đã kiểm tra, tag phù hợp như v1.1.0-rc.1. Build và đóng gói từ tag cuối cùng nếu cần manifest trùng commit GitHub. Commit build cục bộ và commit do upload trình duyệt tạo ra có thể khác nhau.

Chỉ đưa gói Windows công khai không có seed riêng và checksum vào Releases công khai. Gói có danh sách 27 người chỉ bàn giao nội bộ cho người được phép. Không sửa tay manifest để giả commit hoặc kết quả kiểm thử.

Xem [kiểm chứng](VERIFICATION_1.1.0.md), [nghiệp vụ nhân viên](PERSONNEL_1.1.0.md) và [kiến trúc](ARCHITECTURE.md).
