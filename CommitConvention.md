# 📌 Commit Convention

Để dễ quản lý và tránh conflict, tuân thủ mẫu:

Sử dụng chuẩn Conventional Commits để commit rõ ràng, dễ đọc và dễ tạo changelog.

Format:
type(scope?): subject
[BLANK LINE]
body (tuỳ chọn)
[BLANK LINE]
footer (tuỳ chọn, ví dụ: BREAKING CHANGE: ... hoặc closes #123)

Common types:
- feat: thêm tính năng
- fix: sửa lỗi
- docs: tài liệu
- style: format/code style không ảnh hưởng logic
- refactor: refactor code (không thêm tính năng, không sửa lỗi)
- perf: tối ưu hiệu năng
- test: thêm/sửa test
- chore: công việc không ảnh hưởng src (build, config)
- ci: thay đổi cấu hình CI

Ví dụ:
- feat(fpgrowth): build FP-Tree algorithm
- fix(backend): handle empty playlist data
- feat(frontend): show recommended tracks UI
- docs: update dataset description
- chore: add sample music dataset

Ghi chú:
- Viết subject ở dạng câu lệnh (imperative), tối đa ~72 ký tự.
- Nếu cần mô tả chi tiết, thêm body.
- Đóng issue sử dụng footer: "closes #<issue>".

## Branching (quy ước tạo nhánh)

Branch chính:
- main: mã production luôn ổn định

Branch tạm thời:
- feature/<name>/backend-<desc>
  - Ví dụ: feature/truong/backend-fpgrowth
- feature/<name>/frontend-<desc>
  - Ví dụ: feature/thao/frontend-recommend-ui
- fix/<name>/<desc>
  - Dùng khi sửa gấp trên main

Quy trình cơ bản:
1. Tạo branch từ main 
2. Làm việc, commit theo convention ở trên.
3. Push và tạo Pull Request vào main 
4. PR phải có mô tả, liên kết issue (nếu có) và review trước khi merge.