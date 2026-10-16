# AttendSift AI

**Từ tin nhắn Chatwork đến bảng chấm công có thể giải thích và đối chiếu.**

Bộ phận AI · Đặng Gia Khánh · Phiên bản 1.1.0 · Bản ứng viên phát hành

[Chạy trên Windows](docs/INSTALL_WINDOWS.md) · [Nhân viên và CTV](docs/PERSONNEL_1.1.0.md) · [Kiến trúc](docs/ARCHITECTURE.md) · [Đánh giá lựa chọn](docs/ARCHITECTURE_REVIEW_1.1.0.md) · [Kiểm chứng](docs/VERIFICATION_1.1.0.md)

## Cập nhật ngày 16/10/2026

Bản cập nhật bổ sung **nghỉ 30 phút có lương, không làm bù**, cải thiện đối chiếu tên nhân viên và hoàn thiện quy trình **xuất Excel trước, kiểm tra các dòng chưa rõ sau**. Các chức năng đồng bộ Chatwork, quản lý nhân viên, lịch sử và hai chế độ Local/Cloud tiếp tục được giữ.

| Bổ sung | Cách ứng dụng xử lý |
|---|---|
| Nghỉ 30 phút có lương | Tin của chính người xin về sớm ghi rõ “30 phút không làm bù”, có ngày và danh tính đủ căn cứ: ghi 30 phút có lương, không cộng vào phút thiếu giờ, OT hoặc ngày nghỉ |
| Ngày nghỉ thực tế | Chỉ ghi ngày có tin báo phù hợp; không tự điền ngày trống hoặc yêu cầu báo liên tục |
| Đối chiếu nhân viên | Tách người và thời lượng từ tin nguồn trước; đối chiếu họ tên, tên đệm + tên hoặc tên thường dùng với danh sách chính thức |
| Tên trùng hoặc bằng chứng mâu thuẫn | Giữ dòng ở sheet `4_CAN_KIEM_TRA`, chưa cộng vào tổng công; tài khoản người báo hộ không xác minh danh tính cả nhóm |
| Xuất và kiểm tra | Xuất được workbook khi còn dòng cần đối chiếu; mở lại phiên để sửa, xác nhận và xuất bản đã cập nhật |

Ví dụ giả lập: nhân viên báo “Em xin phép về sớm 30 phút không làm bù” vào ngày 12/10 và 14/10 thì ghi **2 sự kiện, tổng 60 phút nghỉ có lương**; không tự tạo sự kiện ngày 13/10. Tin đi trễ 30 phút hoặc về sớm 45 phút không tự áp dụng quy tắc này.

Xem [chính sách nghỉ 30 phút có lương](docs/CHINH_SACH_NGHI_30_PHUT_CO_LUONG.md), [mẫu tin báo công](docs/MAU_BAO_CAO_CHAM_CONG.md) và [kết quả kiểm tra bản cập nhật](docs/UPDATE_2026-10-16.md). Tạo phiên phân tích mới để dùng quy tắc mới; bản Windows cần được đóng gói lại khi mã nguồn thay đổi.

## Bắt đầu từ công việc của người sử dụng

Người phụ trách cần biết ai đã báo công, báo cho ngày nào, thuộc nhóm nào và vì sao hệ thống tính như vậy. AttendSift AI tập trung vào chuỗi công việc đó: giữ tin gốc, hỗ trợ phân tích, đối chiếu danh sách nhân viên, để người dùng xác nhận trường hợp chưa rõ và xuất Excel.

AI hỗ trợ đọc nội dung. Danh sách nhân viên và các quy tắc nghiệp vụ quyết định cách phân loại. Người phụ trách giữ quyền sửa và xác nhận trước khi dùng kết quả chính thức. Dòng chưa đủ bằng chứng được giữ riêng trong Excel và chưa cộng vào tổng công.

## Ba điểm đáng chú ý

**Truy được nguồn.** Mỗi dòng có Source ID để đối chiếu. Nội dung gốc được giữ riêng với phần diễn giải. Một tin báo nhiều người hoặc nhiều ngày có thể tạo nhiều dòng, nhưng không chia OT của người này cho người khác.

**Giữ được ngữ cảnh của báo cáo cũ.** Mỗi phiên lưu danh sách nhân viên tại thời điểm tạo. Thêm, sửa hoặc ngừng hoạt động sau đó không tự viết lại kết quả cũ. Muốn dùng danh sách mới, tạo phiên mới.

**Biết khi nào cần hỏi lại.** Người có danh tính rõ nhưng không thuộc danh sách chính thức được xếp CTV. Tên trùng hoặc thiếu bằng chứng được đưa vào kiểm tra. Người khớp danh sách chính thức nhưng tin ghi CTV vẫn giữ nhóm nhân sự theo danh sách, đồng thời yêu cầu đối chiếu sự kiện trước khi tính công.

## Quy trình trong năm tab

| Tab | Bạn thực hiện |
|---|---|
| Đồng bộ | Lấy tin nhắn, kiểm tra kỳ và dữ liệu nguồn |
| Nhân viên | Thêm, sửa, ngừng hoạt động; nhập danh sách riêng và tên thường dùng |
| Xuất chấm công | Phân tích và xuất Excel; mở lại phiên để đối chiếu, sửa và xác nhận dòng chưa rõ |
| Lịch sử | Xem phiên cũ, hoạt động và báo cáo đã lưu |
| Thiết lập | Kết nối Chatwork, AI và lịch đồng bộ |

Tên thường dùng cần được người quản trị xác nhận. Với hai người cùng tên, nên dùng thêm tên đệm trong Chatwork. Khi bảng nhân viên trống, ứng dụng yêu cầu xác nhận rõ trước khi tiếp tục phân loại CTV.

## Đầu ra: một workbook, năm sheet

| Sheet | Mục đích |
|---|---|
| `1_TIN_NHAN_GOC` | Bằng chứng tin nhắn |
| `2_CHAM_CONG` | Chi tiết nhân viên chính thức |
| `3_TONG_KET` | Tổng hợp nhân viên chính thức |
| `4_CAN_KIEM_TRA` | Dòng chưa đủ căn cứ, lý do cần kiểm tra và dấu vết xác nhận hoặc loại dòng; dòng chưa xác minh không tính công |
| `5_CTV` | Chi tiết CTV, tin gốc và tổng OT/ngày nghỉ theo người |

OT CTV không cộng vào tổng chính thức. Các phiên cũ giữ chính sách và định dạng cũ; không tự chuyển báo cáo bốn sheet thành năm sheet.

Ví dụ giả lập: “Lan Demo OT 1h; An Demo (CTV) OT 2h” tạo OT chính thức 60 phút nếu Lan Demo thuộc danh sách và OT CTV 120 phút cho An Demo.

Theo quy tắc hiện tại, tin chỉ xin nghỉ hoặc phép năm được giữ nguyên văn ở sheet tin nguồn, không tự cộng ngày nghỉ từ suy đoán của AI. Nghỉ bù OT và các sự kiện đo được như tăng ca, đi trễ, về sớm được xử lý theo căn cứ riêng.

Để theo dõi nghỉ 30 phút có lương, báo cáo có thêm cột **AB** ở `2_CHAM_CONG`, cột **O** ở `3_TONG_KET` và cột **L** ở `5_CTV`. Các cột trước đó giữ vị trí. Thông tin ở sheet CTV phục vụ đối chiếu, không tự quyết định tiền lương CTV.

## Chọn nơi sử dụng

| | Windows Local | Website Cloud |
|---|---|---|
| Mở | ChamCong.exe hoặc mã nguồn Python | Trình duyệt có đăng nhập |
| Dữ liệu | SQLite tại máy | PostgreSQL trên Neon |
| Lịch | Task Scheduler, máy bật và tài khoản đăng nhập | Vercel Cron |
| Danh sách | Nhập riêng; gói bàn giao nội bộ có thể kèm file khởi tạo | Người quản trị nhập JSON tại tab Nhân viên |
| Thời hạn lưu | Người vận hành quản lý | Dữ liệu nghiệp vụ theo chính sách 3 tháng; giữ danh sách nhân viên |

Hai bản không tự chia sẻ database hoặc khóa. Bản Local vẫn gửi nội dung cần phân tích tới dịch vụ AI đã chọn. Internet, quyền truy cập và quota API cần được người sử dụng chuẩn bị.

## Cài trên máy người nhận

Với gói nội bộ dễ dùng: giải nén ZIP vào thư mục có quyền ghi rồi mở `ChamCong.exe` ngay ở ngoài cùng. Không cần Python. Giữ file `NHAN_VIEN_RIENG.json` bên cạnh EXE nếu được bàn giao danh sách ban đầu; file này chỉ khởi tạo khi chưa có danh sách, không ghi đè chỉnh sửa.

Vào Thiết lập để nhập khóa của người sử dụng. Kiểm tra bằng dữ liệu thử và nghiệm thu Excel trước khi dùng thực tế. EXE chưa ký số; nếu bị chặn, nhờ IT kiểm tra nguồn và checksum.

Chạy từ mã nguồn: Python 3.11 x64 → `CAI_DAT_WINDOWS.bat` → `KIEM_TRA_LOCAL_WINDOWS.bat` → `CHAY_LOCAL_WINDOWS.bat`. Xem [hướng dẫn Windows](docs/INSTALL_WINDOWS.md).

## Kiến trúc vừa đủ để bảo trì

Ứng dụng được tổ chức theo các mô-đun trong một gói triển khai cho mỗi chế độ. Quy tắc nhân viên và ngày nghỉ dùng chung; Local và Cloud có lớp lưu trữ riêng. Cách này giảm chi phí vận hành, nhưng các luồng phân tích cũ vẫn cần được kiểm thử đồng thời khi thay đổi.

[Sơ đồ kiến trúc](docs/ARCHITECTURE.md) giải thích từ góc nhìn người dùng đến mô-đun. [Bản đánh giá](docs/ARCHITECTURE_REVIEW_1.1.0.md) trình bày nguồn tham khảo, lựa chọn giữ lại, ưu điểm, giới hạn và thời điểm nên thay đổi. Không coi tên một xu hướng kiến trúc là bằng chứng chất lượng.

## Những điều cần hiểu trước khi dùng

Chatwork có thể chỉ trả cửa sổ 100 tin gần nhất. Đồng bộ thành công không chứng minh đầy đủ lịch sử tháng. AI có thể nhầm, và người không nằm trong danh sách có thể là nhân viên chưa được nhập; hãy cập nhật danh sách và kiểm tra căn cứ phân loại.

Cloud dọn dữ liệu quá hạn theo [chính sách 3 tháng](docs/RETENTION_3_MONTHS.md). Tải báo cáo cần giữ lâu dài trước hạn. Thời hạn lưu không bảo đảm luôn vừa quota miễn phí.

Xem [báo cáo kiểm chứng](docs/VERIFICATION_1.1.0.md) để phân biệt điều đã thử với điều còn cần nghiệm thu trên máy nhận, API thật, Microsoft Excel và PostgreSQL staging.

## Quyền riêng tư và hỗ trợ

Danh sách nhân sự, khóa, database và Excel thật không thuộc bộ mã nguồn công khai. Gói nội bộ có danh sách là dữ liệu riêng, chỉ chuyển cho người được phép. Kiểm thử dùng người giả lập.

Khi báo lỗi, gửi phiên bản, bước tái hiện và thông báo đã che dữ liệu. Xem [SECURITY](SECURITY.md), [CONTRIBUTING](CONTRIBUTING.md) và [quyền sử dụng](LICENSE_DECISION.md). Dự án chưa cấp giấy phép mã nguồn mở và không liên kết chính thức với Chatwork hoặc nhà cung cấp AI.
