# Developer guide — cấu trúc hiện tại

Mục tiêu: giữ code ứng dụng Local ở `main.py` + `src/`, không tạo nhánh source copy bên ngoài làm lỗi đồng bộ. Mọi tính năng công khai trên README cần đối chiếu được với code hoặc test.

## Khởi chạy và môi trường

- Windows x64 + Python 3.11, `CAI_DAT_WINDOWS.bat`, `CHAY_LOCAL_WINDOWS.bat`.
- `src/app/launcher.py` mở local server và dùng `pywebview` nếu môi trường hỗ trợ; fallback tới browser.
- `src/app/server.py` chứa API local bind `127.0.0.1`. SQLite truy cập thông qua `src/models/database.py`.
- `src/adapters/` gồm Chatwork và AI; `src/services/` xử lý sync, phân tích, đối chiếu, xác thực, xuất.
- `src/utils/excel_export.py` lấy mẫu `templates/template.xlsx`. Không tự bổ sung mẫu không được kiểm tra.
- `cloud/` triển khai Web là *tùy chọn riêng*, cần PostgreSQL và xác thực phù hợp, không phải bản Local mặc định.

## Giữ đúng nghiệp vụ

- Một tin có nhiều người hoặc nhiều ngày phải ra một event riêng cho từng người/ngày/loại; thời lượng OT phải giữ đúng cho từng người.
- `event_policy.py` xử lý tin `(CTV)` và phép năm theo chính sách nguồn-only của dự án; không tự loại tên ngắn chỉ vì registry chưa có.
- `source_reconciliation.py` không thay thế nội dung chứng cứ và không tự tin tuyệt đối vào AI output.
- Viết test fixture giả lập; tên người thật không được đưa vào public test.

## Chạy test

```shell
python -m compileall -q main.py app.py cloud src tools
python -m pytest -q
python tools/release_audit.py .
```

Toàn bộ test phải chạy trong đúng môi trường phù hợp. Một số test phụ thuộc Windows DPAPI, Flask/werkzeug và WebView. Xem `docs/VERIFICATION_2026-10-14.md` để biết chính xác những gì đã chạy trong đợt tạo hồ sơ, không dùng thống kê cũ như tiêu chí chứng nhận.

## Thay đổi & phát hành

1. Thêm test tái hiện vấn đề, ưu tiên tình huống mơ hồ.
2. Cập nhật code và tài liệu, không thay đổi quy tắc chấm công ngầm.
3. Rà soát secret, screenshot, third-party assets, license.
4. Chạy trên Windows sạch và mở Excel bằng Microsoft Excel.
5. Chỉ sau nghiệm thu mới gắn nhãn release ổn định.
