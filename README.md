# ChamCongChatwork

**Ứng dụng chấm công Local cho Windows — chuyển báo cáo Chatwork thành dữ liệu chấm công có thể đối chiếu.**

[English](README_EN.md) · [Cài đặt Windows](docs/INSTALL_WINDOWS.md) · [Kiến trúc](docs/ARCHITECTURE.md) · [Kiểm thử](docs/TESTING.md) · [Bảo mật & quyền riêng tư](docs/PRIVACY_AND_SECURITY.md)

> **Trạng thái: Release Candidate / demo kỹ thuật.** Mã nguồn có luồng xử lý và kiểm thử tự động; **chưa được chứng nhận chạy ổn định trên mọi máy Windows**, chưa xác minh đầy đủ kết nối Chatwork/AI thật và bản EXE trên máy sạch. Các hình ảnh dưới đây được che thông tin cá nhân; không phải dữ liệu thử nghiệm công khai có thể khôi phục.

## Vấn đề thực tế

Các nhóm làm việc báo cáo tăng ca, nghỉ hoặc về sớm bằng tin nhắn tự nhiên. Một tin có thể nêu **nhiều nhân viên, nhiều ngày và nhiều thời lượng khác nhau**. Đọc thủ công dễ thiếu người, nhầm ngày, cộng sai OT và khó đối chiếu lại nguồn.

**Giải pháp:** Đồng bộ tin Chatwork → phân tích sự kiện → đối chiếu với tin gốc và quy tắc nghiệp vụ → cho người phụ trách kiểm tra trường hợp chưa chắc chắn → xuất Excel 4 sheet. Mỗi sự kiện cần được liên kết tới `Source ID` ban đầu.

## Giao diện và minh chứng

![Giao diện Local - dữ liệu nhạy cảm đã được ẩn](docs/images/01-local-interface-redacted.png)

| Tin gốc | Chấm công chi tiết | Tổng kết |
|:---:|:---:|:---:|
| ![Nguồn tin, dữ liệu được ẩn](docs/images/02-source-sheet-redacted.png) | ![Chi tiết, dữ liệu được ẩn](docs/images/03-attendance-sheet-redacted.png) | ![Tổng kết, dữ liệu được ẩn](docs/images/04-summary-sheet-redacted.png) |

*Ảnh chụp giao diện thực tế (10/2026); dữ liệu hàng nhân sự, mã tin, nội dung riêng tư đã được che hoàn toàn. Bản công khai không kèm video gốc hoặc file Excel có thông tin nhân viên. Xem [hướng dẫn chuẩn bị demo](docs/DEMO_GUIDE.md).*

## Điểm nổi bật có trong mã nguồn

- **Một tin → nhiều dòng:** tách theo `nhân viên × ngày × loại sự kiện`; mỗi người nhận **đủ số phút OT của mình**, không chia tổng phút cho số người.
- **Tin nhiều ngày:** ngày sự kiện lấy từ nội dung, có thể khác ngày gửi tin.
- **Bằng chứng:** lưu bản tin gốc và tham chiếu `Source ID`; các sự kiện AI suy đoán không có bằng chứng phải được đối chiếu.
- **Quy tắc đã thống nhất:** tin xin **phép năm** và người được gắn rõ `(CTV)` chỉ giữ nguồn, không tính vào OT/bảng công chính thức theo chính sách của phiên bản này. Tên ngắn không mặc nhiên bị loại nếu thiếu mã nhân viên.
- **Xuất báo cáo:** `1_TIN_NHAN_GOC`, `2_CHAM_CONG`, `3_TONG_KET`, `4_CAN_KIEM_TRA`. File chấm công chính được lưu vào thư mục **Downloads** trên máy Local theo cấu hình Windows.
- **Local-first:** giao diện chạy với Python/Flask qua `127.0.0.1`, dữ liệu SQLite riêng từng máy, cấu hình khóa tại máy sử dụng. Không cần server cloud trong chế độ Local.
- **Có kiểm thử nguồn:** bộ test dưới `tests/`, workflow kiểm thử và build Windows ở `.github/workflows/ci.yml`.

## Ví dụ nghiệp vụ bằng dữ liệu GIẢ LẬP

Tin Chatwork giả lập (không phải tin nhân sự thật):

```text
Nhóm Demo: ngày 5/10
Lan OT 1h, Minh + Bình OT 2h

Ngày 7/10
Lan OT 1h30
Minh OT 30ph
Nam OT 1h
```

| Ngày sự kiện | Nhân viên | Loại | Số phút OT |
|---|---|---|---:|
| 05/10 | Lan | Tăng ca | 60 |
| 05/10 | Minh | Tăng ca | 120 |
| 05/10 | Bình | Tăng ca | 120 |
| 07/10 | Lan | Tăng ca | 90 |
| 07/10 | Minh | Tăng ca | 30 |
| 07/10 | Nam | Tăng ca | 60 |

**Sáu dòng OT — một tin nguồn.** Để xác nhận ví dụ khác hoặc trường hợp mơ hồ, chương trình phải kiểm tra bằng chứng; không suy đoán họ tên đầy đủ khi không có cơ sở.

## Chạy nhanh trên Windows 10/11 x64

Yêu cầu: **Python 3.11 x64** (khuyến nghị; có thể dùng 3.12 tùy thư viện), Internet trong lần cài đầu và khi gọi Chatwork/AI API.

1. Tải repository bằng **Code → Download ZIP**, giải nén vào thư mục có quyền ghi (ví dụ `C:\ChamCongChatwork`).
2. Chạy `CAI_DAT_WINDOWS.bat` (tạo `.venv` và cài phụ thuộc).
3. Chạy `KIEM_TRA_LOCAL_WINDOWS.bat` nếu cần kiểm tra môi trường.
4. Chạy `CHAY_LOCAL_WINDOWS.bat`, mở giao diện `http://127.0.0.1:8766`.
5. Vào **Thiết lập** nhập API key/Room ID của chính bạn; thử với dữ liệu không nhạy cảm trước khi sử dụng thật.

Xem [hướng dẫn chi tiết, khắc phục lỗi và chuyển máy](docs/INSTALL_WINDOWS.md). **Tải ZIP không đồng nghĩa đã có EXE.** Muốn tạo EXE hãy build bằng `TAO_EXE_WINDOWS.bat` trên Windows hoặc workflow Windows; sau đó kiểm thử file nhận được trên máy khác.

## Cấu trúc repository

```text
ChamCongChatwork/
├── main.py, src/app/             # ứng dụng Local, HTTP loopback, lifecycle
├── src/adapters/                 # Chatwork / nhà cung cấp AI
├── src/services/                 # đồng bộ, chính sách sự kiện, xác thực, xuất
├── src/models/                   # SQLite và migrations
├── src/utils/                    # xử lý tin nhắn, Excel, bảo mật
├── templates/                    # giao diện & mẫu workbook 4 sheet
├── static/                       # assets giao diện
├── tests/                        # kiểm thử logic và xuất file
├── tools/                        # kiểm tra phát hành / cài đặt
├── docs/                         # tài liệu và ảnh đã che dữ liệu
├── cloud/                        # tùy chọn Web hosting, KHÔNG cần khi chạy Local
├── .github/workflows/           # CI + Windows build (chưa nghiệm thu EXE)
└── *_WINDOWS.bat                 # cài, chạy, kiểm tra, build
```

## Quy trình, giới hạn & chất lượng

- [Kiến trúc và luồng xử lý](docs/ARCHITECTURE.md) · [Quy tắc Excel và nghiệp vụ](docs/BUSINESS_RULES.md) · [Ma trận tính năng](docs/FEATURE_MATRIX.md)
- [Cách chạy test, điều đã xác minh](docs/TESTING.md) · [Trạng thái phát hành](docs/RELEASE_CHECKLIST.md) · [Roadmap](docs/ROADMAP.md)
- [Hướng dẫn ghi hình demo có dữ liệu giả](docs/DEMO_GUIDE.md) · [Tư duy thiết kế / portfolio](docs/PORTFOLIO_STORY.md)

Ứng dụng dùng dữ liệu chat nhạy cảm. **Không đưa `data/`, `.env`, credentials, log, Excel người thật hay video quay tin thật lên GitHub.** Nếu public repository, phải kiểm tra cả *toàn bộ lịch sử commit*, không chỉ trạng thái mới nhất. Xem [Privacy & Security](docs/PRIVACY_AND_SECURITY.md).

## Phạm vi sử dụng, bản quyền và đóng góp

Dự án trình bày như một **sản phẩm cá nhân đang hoàn thiện**; chưa tuyên bố có chứng nhận độc lập, kiểm định bảo mật hay độ chính xác AI tuyệt đối. Tác giả/chủ sở hữu cần **chọn giấy phép** trước khi cho phép người khác tái sử dụng: hiện **chưa kèm giấy phép mở** (xem [LICENSE_DECISION.md](LICENSE_DECISION.md)).

Các đề xuất thay đổi và báo cáo lỗi có thể theo [CONTRIBUTING.md](CONTRIBUTING.md) và [SECURITY.md](SECURITY.md). Ứng dụng không liên kết chính thức với Chatwork hay nhà cung cấp AI; tên sản phẩm bên thứ ba là để mô tả tích hợp.
