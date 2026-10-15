# Đăng mã nguồn và bàn giao bản 1.0.2

## Ba đầu ra

| Đầu ra | Dùng cho |
|---|---|
| Thư mục cập nhật GitHub | Kéo nội dung bên trong lên gốc repository, giữ đường dẫn tương đối |
| `AttendSift-AI_Source_1.0.2.zip` | Mã nguồn đầy đủ, không có .git, EXE, khóa hoặc database vận hành |
| `AttendSift-AI_Windows_1.0.2.zip` | Portable có EXE, hướng dẫn, nguồn và manifest |

## Cập nhật bằng trình duyệt

1. Repository → Add file → Upload files trên nhánh main.
2. Mở thư mục cập nhật bằng File Explorer, chọn nội dung bên trong và kéo vào khung upload. Không kéo thư mục bao ngoài.
3. Kiểm tra đường dẫn: `README.md`, `docs/INSTALL_WINDOWS.md`... phải nằm đúng vị trí.
4. Commit, kiểm tra Actions và deployment.
5. Với bản sửa UTF-8, tải lại các tệp đã sửa rồi kiểm tra tiếng Việt trên README.

Không đưa EXE, ZIP hoặc database vào cây mã nguồn. ZIP Windows dùng làm asset trong Releases.

## Phát hành Windows

1. Repository → Releases → Draft a new release.
2. Chọn đúng commit và tag `v1.0.2-rc.1`.
3. Tiêu đề: `AttendSift AI 1.0.2 — Windows & Cloud`.
4. Dùng [release notes](RELEASE_NOTES_1.0.2.md), đính kèm ZIP và checksum.
5. Giữ nhãn pre-release đến khi hoàn thành [biên bản nghiệm thu](HANDOVER_ACCEPTANCE.md).

Manifest ghi commit nguồn của bản build cục bộ. Tải bằng trình duyệt tạo commit GitHub khác. Muốn liên kết commit chính xác cho phát hành công khai, build và đóng gói từ tag GitHub cuối cùng; không sửa tay manifest để giả trùng commit.

## Tái tạo gói

```powershell
python -m pip install -r requirements-build.txt -r requirements-web.txt
python -m pytest -q
node tests/test_cloud_message_ui.cjs
python -m PyInstaller --noconfirm --clean --distpath release --workpath build ChamCong.spec
```

Dùng đúng môi trường Python. Node chỉ cần cho kiểm thử UI. Thử EXE bằng `--check-runtime REPORT.json` và `--headless --port PORT`; đối chiếu HTTP local. Báo cáo verification chỉ ghi đạt khi thực sự đạt và phải có SHA256 đúng EXE đã thử.

```powershell
python tools/package_windows.py --exe release/ChamCong.exe --output release/AttendSift-AI_Windows_1.0.2.zip --verification release/verification.json
```

Công cụ dùng danh sách Git theo dõi và yêu cầu mã nguồn đã commit sạch. Kiểm tra ZIP không chứa dữ liệu vận hành. Quyền sử dụng và phân phối cần được chủ sở hữu xác nhận; dự án chưa cấp giấy phép mã nguồn mở.
