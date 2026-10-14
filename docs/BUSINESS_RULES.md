# Quy tắc chấm công được triển khai (không phải quy định pháp luật)

| Đầu vào | Quy tắc kỳ vọng | Lưu ý kiểm tra |
|---|---|---|
| Một tin nêu 3 người OT 2h | 3 dòng, **mỗi người 120 phút** | Không chia 120/3 và không gán cho người gửi |
| Tin có cả ngày A và B | Dòng ngày A/B riêng theo ngữ cảnh | Ngày gửi không phải ngày sự kiện |
| Tin nêu hai nhóm khác thời lượng | Áp phút tương ứng từng nhóm | Không sao chép thời lượng cuối cho nhóm khác |
| Báo cáo cho người thứ ba | Ghi nhân viên được nêu, không mặc định người gửi | Đối chiếu tên ngắn/tài khoản cẩn thận |
| Họ tên viết tắt | Giữ tên gốc nếu có bằng chứng OT | Không tự đoán mã nhân viên hoặc nhập nhằng danh tính |
| `(CTV)` rõ ràng | Chỉ lưu tin nguồn theo chính sách của dự án | Tên trần như `Ny`/`Cầm` **không mặc định** là CTV |
| Đơn xin phép năm | Chỉ ghi nhận nguyên văn tin nguồn, không tính ngày phép | Quy tắc do người sử dụng yêu cầu, không phải chính sách chung |
| Tin không có tuyên bố chấm công | Chỉ lưu nguồn | Không tạo công/OT do AI suy diễn |

**Về “nguyên văn”:** lớp lưu trữ tin gốc dùng nội dung Chatwork. Dòng hiển thị Excel có thể loại phần **tiêu đề người gửi bị sao chép trùng** ở đầu tin. Không nên tuyên bố bản Excel bảo toàn 100% byte-for-byte của mọi dữ liệu nếu chưa kiểm thử đối chiếu. Nếu cần bản chứng cứ bất biến, kiểm tra `body` và hash của bản ghi trong cơ sở dữ liệu gốc.

**Chất lượng nguồn:** Chatwork API hiện chỉ tải được một cửa sổ tin nhất định qua từng lần truy vấn; khi lịch sử trước đó chưa được thu thập đầy đủ, xuất Excel phải ghi rõ rủi ro thiếu dữ liệu. Không lấy khoảng trống nguồn làm bằng chứng vắng mặt.
