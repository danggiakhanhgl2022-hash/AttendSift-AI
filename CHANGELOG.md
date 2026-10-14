# Changelog

## Unreleased — GitHub portfolio documentation pass (2026-10-14)

- Viết lại README tiếng Việt, bổ sung README English và bộ tài liệu kiến trúc, nghiệp vụ, bảo mật, kiểm thử, demo, portfolio.
- Thêm bốn ảnh đã che toàn bộ dữ liệu hàng nhân sự; **không** đưa video thô và Excel nhân viên vào repository.
- Thay các họ tên đầy đủ từ fixture kiểm thử bằng tên giả để giảm nguy cơ lộ thông tin khi public; giữ logic đặc trưng của test. Chạy lại bộ test nghiệp vụ.
- Nâng pin `requests` từ `2.31.0` lên `2.32.5` trong ba file requirements để không giữ phiên bản cũ được nêu trong cảnh báo bảo mật công khai. Chưa chạy kiểm thử mạng/API thật và audit dependency đầy đủ.
- Thêm Dependabot và giấy tờ quyết định giấy phép.

**Không thay đổi luồng nghiệp vụ chính hay tuyên bố đã phát hành một EXE đã nghiệm thu.** Đây là bản chuẩn bị repository, chưa phải bản production chứng nhận.
