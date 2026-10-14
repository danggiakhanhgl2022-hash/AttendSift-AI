# Phương pháp kiểm thử và bằng chứng

## Những gì đã thực sự chạy trong đợt chuẩn bị portfolio

- Mã Python: `python -m compileall -q main.py app.py cloud src tools`.
- Kiểm tra cấu trúc gói và tệp bị cấm bằng `python tools/release_audit.py .`.
- Kiểm thử nhóm nghiệp vụ chạy bằng `pytest` trên Linux; kết quả thực đo trong lần đóng gói được ghi tại `docs/VERIFICATION_2026-10-14.md`.
- Đầu vào kiểm thử là các fixture/tin nhắn giả lập hoặc đã ẩn danh; không phải đo trên toàn bộ lịch sử công ty.

## Tự chạy test

```powershell
# Trong thư mục project đã cài môi trường
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
# Kiểm tra riêng nghiệp vụ OT và Local
.venv\Scripts\python.exe -m pytest -q tests/test_policy_october_2026_acceptance.py tests/test_multi_employee_screenshots.py tests/test_downloads_export.py
```

Một số test phụ thuộc Windows DPAPI, WebView, Flask hoặc môi trường native; không coi các bài *skip* là đã vượt qua. Khi CI Windows thật chạy, phải lưu link tới GitHub Actions run thành công và screenshot thủ công.

## Tiêu chuẩn nghiệm thu phát hành (chưa hoàn tất)

1. Cài Python + `.bat` trên Windows sạch.
2. Build/khởi chạy EXE từ runner Windows, nhận đủ dependencies và mở được UI.
3. Kiểm thử API Chatwork thật với môi trường được cấp quyền; kiểm tra giới hạn lịch sử và trường hợp đồng bộ lại.
4. Kiểm tra xử lý **1 tin nhiều người/nhiều ngày**, OT mỗi người, không tạo tên mơ hồ.
5. Mở Excel 4 sheet bằng **Microsoft Excel** không `[Repaired]`; kiểm tra format, giá trị và nội dung nguồn.
6. Kiểm tra bản quyền, riêng tư, dữ liệu và khả năng khôi phục backup.

Khi những bước này chưa có chứng cứ, chỉ ghi **release candidate/technical preview**.
