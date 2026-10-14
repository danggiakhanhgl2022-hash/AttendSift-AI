# Các bước đưa lên GitHub để trình bày dự án

1. Trên GitHub tạo repository **Private** tên `ChamCongChatwork` để rà soát trước. Không chọn tạo sẵn README/.gitignore nếu dùng gói này.
2. Tải/giải nén gói ZIP tại máy của bạn; đảm bảo đang ở thư mục có `README.md` và `.gitignore`.
3. Xem kỹ `docs/PRIVACY_AND_SECURITY.md`, các fixture thử nghiệm và nguồn ảnh trước khi đổi sang Public.
4. Mở Git Bash trong thư mục:

```shell
git init
git add README.md README_EN.md CHANGELOG.md LICENSE_DECISION.md CONTRIBUTING.md SECURITY.md \
  .github .gitignore .gitattributes .python-version VERSION \
  *.py src cloud static templates tests tools docs *.bat requirements*.txt \
  ChamCong.spec vercel.json pytest.ini
git status --short
git diff --cached --stat
git commit -m "Prepare documented local-first attendance portfolio"
git branch -M main
git remote add origin https://github.com/YOUR_USER/ChamCongChatwork.git
git push -u origin main
```

Hãy đối chiếu những file `git add` thực sự tồn tại trước khi chạy; `.gitignore` cũng cần kiểm tra thủ công vì **không bảo vệ những gì đã commit trong lịch sử**. Trong GitHub Settings, bật Dependabot alerts và secret scanning/push protection nếu khả dụng.

5. Dùng nội dung ở `docs/GITHUB_ABOUT_AND_CV.md` cho phần **About**, Topics và giới thiệu portfolio.
6. Để chứng minh khả năng chạy Windows, mở **Actions**: chạy workflow Windows trên branch `main`, kiểm tra log, tải artifact. **Không công bố EXE** cho người khác trước khi cài và kiểm tra thực tế trên máy Windows khác.
7. Chọn LICENSE nếu muốn mở quyền sử dụng; không có giấy phép không đồng nghĩa ai cũng được tự do dùng mã.
8. Chỉ đổi repository sang Public khi đã chắc chắn có quyền công khai mọi dữ liệu, ảnh, file nguồn và license bên thứ ba.

**GitHub Pages không chạy Flask backend hoặc SQLite Local**; repository là nguồn, ứng dụng chạy trên máy Windows sau khi cài đặt.
