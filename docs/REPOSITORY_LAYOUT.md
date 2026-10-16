# Cấu trúc mã nguồn chính thức

Bản dọn được tạo từ GitHub commit `44433c9`, giữ lịch sử Git. Loại 185 file tải trùng hoặc sai thư mục; không xóa dữ liệu nhân sự/database vì các dữ liệu đó không thuộc repository nguồn.

```text
README.md                 Giới thiệu chính, ảnh bìa và đường dẫn tài liệu
app.py                    Điểm vào Cloud, gọi cloud.app.create_app
main.py                   Điểm vào Windows, gọi launcher Local
vercel.json               Cấu hình hosting và cron
ChamCong.spec              Cấu hình đóng gói EXE
*.bat                     Cài đặt, kiểm tra và chạy Windows
requirements*.txt         Thư viện theo môi trường
.github/                  CI và cập nhật dependency
cloud/                    API, xác thực, PostgreSQL và giao diện Cloud
src/                      Mã nghiệp vụ, Local, adapter và scheduler
templates/                HTML Local và mẫu Excel
static/                   Tài nguyên giao diện Local
public/                   Tài nguyên phục vụ hosting
tests/                    Bộ kiểm thử giả lập
tools/                    Kiểm tra và đóng gói
docs/                     Hướng dẫn, hình ảnh, bài phân tích và lịch sử
```

Chỉ có một `README.md` giới thiệu ở gốc. `docs/README.md` và `docs/articles/README.md` là mục lục đúng trong thư mục riêng, không được kéo ra gốc. Ảnh bìa nằm tại `docs/images/story/cover.png`.

Các file như `README (1).md`, `__init__ (2).py`, bản sao `test_*.py` ở gốc, `download` và cache Python đã được loại khỏi cây mã nguồn mới. Tài liệu lịch sử vẫn nằm trong `docs/` để các liên kết cũ còn có thể đối chiếu.

## Kiểm tra đã thực hiện

- 398 kiểm thử Python đạt trên Windows/Python 3.11.9, dữ liệu giả lập.
- Kiểm tra UI JavaScript, cài đặt Local, liên kết/ảnh, UTF-8 và audit gói nguồn đạt.
- `tools/check_repository_layout.py` kiểm tra file đã theo dõi bằng Git; CI từ chối file tải nhầm vào gốc hoặc cache được commit.

Không thay nghiệm thu API thật, PostgreSQL staging, Excel/WPS và máy Windows độc lập. Không tải EXE, ZIP, thư mục `.venv`, database hoặc danh sách nhân viên lên cây nguồn.

Để cập nhật GitHub, dùng Git push/patch giữ nguyên đường dẫn. Chép các file từ mọi thư mục con lên gốc sẽ làm hỏng import, ảnh và cấu hình chạy.
