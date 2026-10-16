# Cơ sở biên tập và đóng gói

Tham khảo ngày 15/10/2026. Đây là tự rà soát dựa trên mã nguồn, tài liệu chính thức và trao đổi công khai; không phải sản phẩm đã được diễn đàn đánh giá hoặc chứng nhận.

## Điểm áp dụng

- README trả lời sản phẩm làm gì, hữu ích cho ai, cách bắt đầu, hỗ trợ và bảo trì; hướng dẫn dài ở docs, liên kết nội bộ tương đối. Nguồn: [GitHub Docs — About READMEs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes).
- EXE/ZIP cho người dùng đi kèm release notes và checksum trong Releases. Nguồn: [GitHub Docs — About releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases).
- Phân biệt gói tự chứa Python với mã nguồn; build theo hệ điều hành và kiến trúc đích. Nguồn: [PyInstaller — Operating mode](https://pyinstaller.org/en/stable/operating-mode.html).

## Tham khảo cộng đồng

[GitHub Community về nội dung README](https://github.com/orgs/community/discussions/177551) được dùng tham khảo cách tổ chức thông tin, không phải tiêu chuẩn bắt buộc.

[Reddit r/learnpython về phân phối EXE](https://www.reddit.com/r/learnpython/comments/1eheyvu/) và [cảnh báo antivirus](https://www.reddit.com/r/learnpython/comments/1mtmhbc/) ghi nhận trải nghiệm khác nhau. Đây là ý kiến cá nhân, không chứng minh gói này an toàn hoặc chắc chắn bị cảnh báo.

Đề xuất áp dụng: ghi rõ EXE chưa ký số, có checksum và bằng chứng runtime, hướng dẫn làm việc với IT, giữ release candidate đến khi nghiệm thu máy đích.
