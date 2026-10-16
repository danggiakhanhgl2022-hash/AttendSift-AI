# Bảo mật và quyền riêng tư khi làm portfolio

Ứng dụng xử lý **tin nhắn nội bộ và dữ liệu nhân viên**. Quyền truy cập GitHub Public **không đồng nghĩa** có quyền công khai dữ liệu Chatwork, tên người hoặc kết quả chấm công.

## Đã làm trong gói portfolio

- Không đóng gói SQLite, khóa DPAPI, `.env` thật, Excel kết quả, log hay backup.
- Ảnh chụp thật được **che opaque** toàn bộ vùng chứa dòng nhân sự/mã tin, không chỉ làm mờ. Video gốc **không** được đưa vào bản công khai.
- File `.env.example` chỉ có tên biến hoặc placeholder. `.gitignore` hạn chế các file runtime nhạy cảm.
- Local HTTP bind loopback `127.0.0.1`; mã API kiểm tra Host, Origin và CSRF cho request sửa đổi.

## Rủi ro còn lại

- Không thể cam kết *không còn bí mật* chỉ bằng regex đơn giản hoặc một vòng quét tên. Trước khi chọn **Public**, cần secret scanning bởi công cụ phù hợp (Gitleaks/GitHub), xem tất cả tệp nhị phân, ảnh, fixture và **toàn bộ git history** nếu repository đã từng được đẩy.
- Nếu token từng bị lộ trên GitHub, phải **thu hồi/đổi token**, xóa khỏi history theo hướng dẫn GitHub, không chỉ sửa commit mới.
- Third-party packages có thể có CVE mới; bật Dependabot/security alerts và kiểm tra version mỗi bản phát hành.
- Không tự mở port loopback ra mạng Internet. Trường hợp cloud cần mô hình xác thực, database, backup, key management riêng.
- Video/screenshots chứa thông tin cá nhân: chỉ dùng tài sản đã che dữ liệu và được phép công bố.

## Bản quyền dữ liệu & giấy phép

Các ảnh đã che nhạy cảm dựa trên ảnh do người sử dụng cung cấp. Bản gốc không được phát tán trong ZIP này. Không dùng logo/nhãn hiệu Chatwork làm dấu hiệu dự án được hãng chứng nhận. **Không có LICENSE open-source mặc định**, quyết định cấp phép do chủ dự án thực hiện.

Tham khảo: [GitHub — sensitive data removal](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository), [About README](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes).
