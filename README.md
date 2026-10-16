# AttendSift AI — Chatwork attendance & overtime

Ứng dụng tham chiếu để đồng bộ tin nhắn Chatwork, phân tích tăng ca (OT), đi trễ, về sớm, làm bù, đối chiếu danh sách nhân viên và xuất **bảng chấm công** trong một file Excel gồm 5 sheet.

**Lưu ý về dữ liệu:** Đây là **mã nguồn công khai, không chứa** token Chatwork, khóa AI, thông tin database, file danh sách nhân viên riêng hoặc dữ liệu tin nhắn thật. Mọi ví dụ trong kho này đều được tạo giả lập. Không đặt thông tin thật vào commit.

## Nguyên tắc xử lý

1. Đọc tin nhắn, tách **đầy đủ từng người, ngày, số phút**. Một báo cáo nhiều người được chia thành từng sự kiện, không chia nhỏ số phút OT chung cho mỗi người.
2. Đối chiếu tên đã trích xuất với danh sách chính thức đang hoạt động. Tên đầy đủ, tên cuối và **tên lót + tên** có thể khớp khi chỉ có một người phù hợp; nếu có nhiều người cùng khớp thì đối chiếu **mã nhân viên hoặc Chatwork ID có bằng chứng**. ID của người gửi báo cáo nhóm không chứng minh danh tính của những người khác.
3. Nếu không tìm được người trong danh sách nhân viên chính thức → phân loại CTV. Tin có thiếu ngày hoặc không đủ bằng chứng được ghi vào sheet cần kiểm tra, không tự tính OT.
4. Tin chỉ xin nghỉ phép năm lưu tại sheet tin nhắn gốc; không tự cộng ngày nghỉ. Xuất Excel trước, kiểm tra lại sau.

## Cấu trúc Excel

| Sheet | Dữ liệu |
|---|---|
| `1_TIN_NHAN_GOC` | Nội dung Chatwork nguyên văn |
| `2_CHAM_CONG` | Sự kiện hợp lệ của nhân viên chính thức |
| `3_TONG_KET` | Tổng hợp công, OT chính thức |
| `4_CAN_KIEM_TRA` | Dòng cần đối chiếu, không tự tính công |
| `5_CTV` | Sự kiện hợp lệ và tổng hợp CTV |

## Cài đặt & vận hành

Cần Python 3.11. Xem [`docs/SETUP.md`](docs/SETUP.md) cho cài Local/Cloud và [`docs/MAU_BAO_CAO_CHAM_CONG.md`](docs/MAU_BAO_CAO_CHAM_CONG.md) cho mẫu tin nhắn chung của công ty. Không commit `.env`; cấu hình thật tại máy người dùng hoặc Environment Variables của dịch vụ triển khai. `.env.example` chỉ có tên biến mẫu.

## Đăng GitHub an toàn

Đọc [`docs/GITHUB_PRIVACY.md`](docs/GITHUB_PRIVACY.md), chạy `python tools/privacy_audit.py .` trước `git add/commit`, rà soát thủ công mã nguồn, ảnh và `git diff --cached`. Không đưa danh sách nhân viên hoặc file Excel lên repository công khai.

Ứng dụng có chức năng phân tích với AI bên thứ ba: cân nhắc chính sách bảo mật và quyền chia sẻ dữ liệu trước khi kết nối hệ thống thật.
