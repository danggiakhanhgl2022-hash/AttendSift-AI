# Nguồn hình và cách tái tạo

Các hình trong thư mục này được tạo cho phần mô tả GitHub ngày 16/10/2026. Không lấy dữ liệu nhân sự từ các ảnh tham chiếu do chủ dự án cung cấp.

| Nhóm | Cách tạo | Ý nghĩa |
|---|---|---|
| `poster-technology-v3.png` | Tạo bằng imagegen; prompt lưu tại `poster-technology-v3-prompt.txt` | Bìa README hiện tại: minh họa kiến trúc Chatwork API → AI → đối chiếu → Excel và nhánh xác nhận; không phải ảnh runtime |
| `cover.svg`, `journey.svg` | SVG viết trực tiếp | Hình mở đầu và luồng thông tin, không phải ảnh runtime |
| `cover.png` | Edge hiển thị SVG bìa ở mật độ điểm ảnh 2× | Bản PNG 2880×1180 dùng trong README; tiêu đề và sơ đồ ví dụ cùng một bố cục |
| `ui-*.png` | Playwright + Edge chụp app Flask Local với SQLite tạm | Giao diện thực của 5 tab, dùng người/phòng/tin giả lập; không phải ảnh Cloud đã triển khai |
| `ui-export-focus.png`, `ui-employees-focus.png` | Chụp trực tiếp vùng thao tác với mật độ điểm ảnh 2× | Chữ dễ đọc hơn khi đặt trong README; không sửa giao diện ứng dụng |
| `01-source.png` … `05-contractors.png` | Xuất workbook bằng mã ứng dụng, đọc giá trị bằng openpyxl, vẽ cột chọn bằng Pillow | Hình giải thích dữ liệu workbook; không phải ảnh Excel/WPS, không nghiệm thu các phần mềm đó |
| `demo-manifest.json` | Khẳng định kiểm tra từ fixture | 180 phút OT chính thức, 60 phút nghỉ có lương, 45 phút OT CTV, 1 dòng tên trùng |

Tất cả tên, nội dung, ID và tên phòng ở bộ hình mới đều giả lập. Các ảnh cũ có hậu tố `redacted` ở thư mục phía trên là tài liệu lịch sử và không phải ảnh chính trong README mới.

## Tạo lại trên máy phát triển

```powershell
python -m pip install -r requirements-dev.txt -r requirements-ui-test.txt
python -m pip install Pillow
python -B tools/build_readme_assets.py --screenshots
```

Máy Windows cần có Microsoft Edge. Nếu chỉ cần ảnh workbook và SVG, bỏ `--screenshots`. Pillow và Playwright chỉ là công cụ tạo tài liệu, không phải yêu cầu cài thêm cho người dùng EXE.

Mã tạo ảnh dùng database tạm, chặn request trình duyệt ra ngoài loopback và thay bộ phân tích bằng fixture. Không truyền token/API key thật vào công cụ này. Ảnh không đủ để xác nhận độ chính xác AI, nghiệm thu WebView2 hoặc khả năng chịu tải.
