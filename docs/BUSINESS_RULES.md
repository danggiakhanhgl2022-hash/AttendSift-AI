# Quy tắc chấm công được triển khai (không phải quy định pháp luật)

| Đầu vào | Quy tắc kỳ vọng | Lưu ý kiểm tra |
|---|---|---|
| Một tin nêu 3 người OT 2h | 3 dòng, **mỗi người 120 phút** | Không chia 120/3 và không gán cho người gửi |
| Tin có cả ngày A và B | Dòng ngày A/B riêng theo ngữ cảnh | Ngày gửi không phải ngày sự kiện |
| Tin nêu hai nhóm khác thời lượng | Áp phút tương ứng từng nhóm | Không sao chép thời lượng cuối cho nhóm khác |
| Báo cáo cho người thứ ba | Ghi nhân viên được nêu, không mặc định người gửi | Đối chiếu tên ngắn/tài khoản cẩn thận |
| Họ tên viết tắt | Giữ tên gốc nếu có bằng chứng OT | Không tự đoán mã nhân viên hoặc nhập nhằng danh tính |
| Danh tính không khớp danh sách chính thức | Xếp CTV theo quy tắc sản phẩm và xuất riêng sheet 5 | Danh sách thiếu có thể phân loại sai; cần quản trị dữ liệu |
| Tên khớp danh sách nhưng nguồn ghi CTV | Giữ nhóm chính thức theo danh sách, đưa sự kiện vào kiểm tra | Chưa cộng công khi còn xung đột |
| Tên khớp nhiều người | Chờ bằng chứng hoặc xác nhận đúng ID | Không dùng ID người báo hộ để xác minh cả nhóm |
| Tin chỉ xin nghỉ hoặc phép năm | Chỉ giữ tin nguồn, không tự cộng ngày nghỉ | Quy tắc hiện tại của sản phẩm, không phải chính sách chung |
| Tự báo về sớm 30 phút không làm bù | Ghi 30 phút có lương khi ngày/người/nội dung đủ căn cứ | Không trừ công, không cộng OT, không tự tạo ngày trống |
| Dòng thiếu căn cứ hoặc kiểm tra không hợp lệ | Xuất ở sheet kiểm tra; chưa cộng vào tổng | Người phụ trách sửa/xác nhận rồi xuất lại |
| Tin không có tuyên bố chấm công | Chỉ lưu nguồn | Không tạo công/OT do AI suy diễn |

**Về “nguyên văn”:** lớp lưu trữ tin gốc dùng nội dung Chatwork. Dòng hiển thị Excel có thể loại phần **tiêu đề người gửi bị sao chép trùng** ở đầu tin. Không nên tuyên bố bản Excel bảo toàn 100% byte-for-byte của mọi dữ liệu nếu chưa kiểm thử đối chiếu. Nếu cần bản chứng cứ bất biến, kiểm tra `body` và hash của bản ghi trong cơ sở dữ liệu gốc.

**Chất lượng nguồn:** Chatwork API hiện chỉ tải được một cửa sổ tin nhất định qua từng lần truy vấn; khi lịch sử trước đó chưa được thu thập đầy đủ, xuất Excel phải ghi rõ rủi ro thiếu dữ liệu. Không lấy khoảng trống nguồn làm bằng chứng vắng mặt.

Các quy tắc này mô tả phiên hiện tại có danh sách nhân viên; nhánh tương thích không có registry có thể giữ cách xử lý CTV cũ. Tạo phiên mới để dùng quy tắc mới. Xem [chính sách nghỉ có lương](CHINH_SACH_NGHI_30_PHUT_CO_LUONG.md) và [AI/bằng chứng](ARCHITECTURE.md).
