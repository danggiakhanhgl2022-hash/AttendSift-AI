# Quy chuẩn viết báo cáo chấm công — mẫu dùng chung

## Tên người báo cáo

- Dùng **tên lót + tên** để tránh nhầm: ví dụ có hai nhân viên cùng tên *Quân* thì ghi **Minh Quân** và **Đức Quân** (chỉ là tên giả lập). Không ghi đơn lẻ “Quân”.
- Tốt nhất ghi họ tên đầy đủ như đã đăng ký trong danh sách nhân viên. Họ tên rút gọn được chấp nhận nếu đối chiếu **duy nhất một hồ sơ**. Nếu vẫn trùng tên, ghi thêm **mã nhân viên** hoặc một ID nội bộ hợp lệ được hệ thống quản lý; không chia sẻ Chatwork ID thật trong tin nhắn công khai nếu không cần thiết.
- Chỉ dùng nhãn “(CTV)” để giúp người đọc; **danh sách nhân viên chính thức đang hoạt động** mới là nguồn phân loại.

## Mẫu tăng ca một người

```text
Báo cáo OT — ngày 16/10/2026
Minh Quân OT 2h30p
Lý do: hoàn tất công việc được giao
```

## Mẫu tăng ca nhiều người

```text
Team Demo — ngày 16/10/2026
Minh Quân + Đức Quân OT 2h
Lan (CTV) OT 1h30p
Lý do: hoàn thiện đầu việc theo kế hoạch
```

Mỗi người trong dòng nhóm có cùng số phút OT ghi tại dòng đó. Nếu thời lượng khác nhau, **tách dòng**. Mỗi ngày khác nhau ghi một tiêu đề ngày hoặc một dòng riêng; không dùng ngày gửi tin để thay cho ngày làm việc.

## Mẫu báo đi trễ, về sớm hoặc làm bù

```text
Báo cáo chấm công — ngày 16/10/2026
Minh Quân về sớm 60 phút; dự kiến làm bù ngày 17/10/2026
Lý do: việc cá nhân
```

Nêu rõ thời gian **đã thực hiện** và thời gian **dự kiến**. Không ghi thời gian dự kiến vào OT thực tế trước khi có xác nhận hoàn thành.

## Mẫu nghỉ phép năm

```text
Đơn xin nghỉ phép năm — ngày 19/10/2026
Người xin nghỉ: Minh Quân
Lý do: việc cá nhân
```

Tin thuần túy xin phép năm chỉ được lưu nguyên văn ở `1_TIN_NHAN_GOC`, không tự cộng ngày nghỉ. Các sự kiện khác được nêu rõ trong cùng tin vẫn cần xem xét riêng.

## Kiểm tra cuối

Phải có **người + ngày/tháng/năm + loại sự kiện + số phút/thời lượng** nếu muốn tự tính. Nếu thiếu hoặc trùng danh tính, hệ thống lưu ở `4_CAN_KIEM_TRA` để rà soát sau; vẫn xuất Excel 5 sheet. Không để tin thật, tên khách hàng, ID hoặc API key vào tài liệu GitHub này.
