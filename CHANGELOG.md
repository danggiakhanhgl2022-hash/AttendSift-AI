# Changelog

## 1.0.2 ? 2026-10-15 (release candidate)

- G?p c?c s?a cloud: hi?n th? tin nh?n, GMT+7, x?c th?c cron v? d?n d? li?u 3 th?ng.
- B? sung h??ng d?n Local/Cloud, b?n giao m?y m?i, release notes v? bi?n b?n nghi?m thu.
- Chu?n h?a t?n AttendSift AI, phi?n b?n 1.0.2 v? b?ng ch?ng ki?m ch?ng.
- G?i Windows portable v? ZIP ngu?n ???c chu?n b? ri?ng; ch?a k? s? hay nghi?m thu m?y ??c l?p.


## Unreleased — GitHub portfolio documentation pass (2026-10-14)

- Viết lại README tiếng Việt, bổ sung README English và bộ tài liệu kiến trúc, nghiệp vụ, bảo mật, kiểm thử, demo, portfolio.
- Thêm bốn ảnh đã che toàn bộ dữ liệu hàng nhân sự; **không** đưa video thô và Excel nhân viên vào repository.
- Thay các họ tên đầy đủ từ fixture kiểm thử bằng tên giả để giảm nguy cơ lộ thông tin khi public; giữ logic đặc trưng của test. Chạy lại bộ test nghiệp vụ.
- Nâng pin `requests` từ `2.31.0` lên `2.32.5` trong ba file requirements để không giữ phiên bản cũ được nêu trong cảnh báo bảo mật công khai. Chưa chạy kiểm thử mạng/API thật và audit dependency đầy đủ.
- Thêm Dependabot và giấy tờ quyết định giấy phép.

**Không thay đổi luồng nghiệp vụ chính hay tuyên bố đã phát hành một EXE đã nghiệm thu.** Đây là bản chuẩn bị repository, chưa phải bản production chứng nhận.
