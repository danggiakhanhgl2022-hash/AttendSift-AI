# Kiểm thử và giới hạn

## Python

```powershell
python -B -m pytest -q -p no:cacheprovider tests
```

405 kiểm thử đã đạt ở bản Local ngày 17/10/2026, gồm 398 kiểm thử nền và 7 kiểm thử bộ đọc workbook. Kiểm tra nguồn, nhân sự, xác nhận, loại dòng, kỳ báo cáo và xuất Excel. Bài mới kiểm tra chính thức/CTV lấy theo sheet, ô công thức thiếu cache, upload có CSRF và không sửa dữ liệu.

## Giao diện

Cài requirements-ui-test.txt trong môi trường có Microsoft Edge:

```powershell
python tools/verify_dashboard_ui.py
python tools/verify_operation_orb_ui.py
python tools/verify_people_summary_ui.py
```

Chạy lần lượt để không tranh GPU. Kiểm thử dùng workbook giả lập; kiểm tra bảng chính thức không bị phân loại API khác ghi đè, CTV riêng, chọn file và trở về file phiên, chuyển động có thay đổi pixel, không còn Operations Room, năm tab còn hoạt động và mobile không tràn ngang.

[Kết quả bảng Excel](verification/workbook-overview.json). POST trong kiểm thử vòng trạng thái được giả lập. POST tải workbook chỉ phân tích trong bộ nhớ, không ghi nghiệp vụ.

## Nguồn và bàn giao

Chạy check_documentation.py, check_release_encoding.py, check_repository_layout.py, release_audit.py và privacy_audit.py trong tools/. EXE được so khớp tài nguyên và chạy --check-runtime.

Kiểm thử headless không thay thế nghiệm thu WebView Windows thật, tài khoản Chatwork/AI thật, tính đầy đủ của kỳ và việc mở workbook trên máy người nhận.

## Phiên bản báo cáo EXE

`verification/archive/exe-v6.0.json` là bằng chứng **lịch sử của V6.0**, không chứng nhận cho EXE V6.2 mới. Trước khi phát hành hoặc gắn nhãn đã nghiệm thu V6.2, phải chạy kiểm tra EXE thực tế và ghi lại SHA-256 trùng với file phát hành.
