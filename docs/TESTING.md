# Kiểm thử và giới hạn bằng chứng — 1.0.2

Kết quả hiện tại ở [báo cáo kiểm chứng](VERIFICATION_1.0.2.md). Báo cáo ngày cũ chỉ mô tả lần chạy tương ứng.

## Chạy lại

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
node tests/test_cloud_message_ui.cjs
python tools/check_local_install.py
python tools/release_audit.py .
python tools/check_release_encoding.py .
```

Cài requirements-build.txt khi build EXE. Môi trường chỉ có dependencies Local có thể thiếu dependencies cloud. Node chỉ cần cho bài test UI, không cần trên máy người nhận.

Fixture dùng dữ liệu giả. Kiểm thử gồm nhiều người/nhiều ngày, bằng chứng nguồn, workbook, HTTP xác thực, cutoff lịch, ngăn nhập lại tin hết hạn và quyền cron. Không tự xóa database production.

## Kiểm tra riêng

- EXE: thư viện và template qua `--check-runtime`; chạy HTTP headless, ghi đúng checksum EXE đã thử.
- Máy nhận: cửa sổ, WebView2, quyền ghi, Downloads và Task Scheduler.
- API thật: Chatwork/AI bằng tài khoản được phép, đối chiếu số tin và quota.
- Microsoft Excel: mở không sửa chữa, kiểm tra giá trị và chính sách.
- Retention: thử SQL trên PostgreSQL staging độc lập.

Không xem skip là đạt hoặc tự chuyển stable khi kiểm thử tự động xanh. Dùng [biên bản bàn giao](HANDOVER_ACCEPTANCE.md).
