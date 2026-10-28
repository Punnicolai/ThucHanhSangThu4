# Lab 06 - Bảo mật với DevSecOps

Bộ mã nguồn thực hành theo lab-06.pdf, gồm pipeline cơ bản và Docusaurus triển khai lên GitLab Pages. Nội dung lý thuyết nằm trong `docs/index.md`.

## Vị trí trong kho GitHub

Bài này nằm tại `bai6/` trong kho `Punnicolai/ThucHanhSangThu4`.
Mở PowerShell ở gốc kho rồi chạy `cd .\bai6` trước các lệnh npm.
Workflow `.github/workflows/bai6-build.yml` ở gốc kho tự build bài 6 và lưu artifact khi push hoặc mở pull request có thay đổi bài 6. Workflow này không triển khai GitLab Pages.
Để chạy đúng phần GitLab trong đề, chép nội dung `bai6/` sang gốc một dự án GitLab riêng rồi làm các bước bên dưới. GitHub không chạy tệp `.gitlab-ci.yml`.

## Chạy tại máy

Cài Node.js từ 20 trở lên (nên dùng Node 22 để đồng nhất CI). Tại thư mục chứa package.json:

```sh
npm ci
npm run build
npm run serve
```

Mở địa chỉ được hiển thị trong terminal. Dừng server bằng Ctrl+C.

## Thực hiện trên GitLab

1. Tạo dự án trống trong tài khoản GitLab, clone về máy. Nếu dự án đã có README, giữ lịch sử Git và sao chép các tệp bài làm vào checkout đó.
2. Chép toàn bộ nội dung thư mục này, bao gồm `.gitlab-ci.yml` và `.gitignore`, vào gốc dự án.
3. Để thực hành 6.2.1, lưu cấu hình mặc định ra ngoài repo, rồi chép `examples/01-basic.yml` thành `.gitlab-ci.yml`. Commit, push và chụp màn hình pipeline cùng log deploy-prod.
4. Với phần 6.2.2, lần lượt dùng `examples/02-first-job.yml`, `examples/03-build.yml`, rồi khôi phục `.gitlab-ci.yml` mặc định. Commit và push sau mỗi bước.
5. Trong Build > Pipelines, kiểm tra job, log build và artifacts. Nếu job pending, kiểm tra runner và hạn mức compute của tài khoản.
6. Trong Deploy > Pages, mở URL thực tế GitLab cung cấp. Cấu hình tự lấy URL này khi build trong CI.

```sh
git add .
git commit -m "Complete lab 06 GitLab CI and Docusaurus"
git push
```

Không chạy git init trong checkout đã clone. Không đưa node_modules, build hoặc token vào Git.

## Điều chỉnh so với đề

- Dùng `npm ci` và lockfile để cài dependency nhất quán.
- Chỉ publish nhánh mặc định; nhánh khác vẫn build để kiểm tra.
- Dùng `pages.publish` rõ ràng theo cú pháp GitLab hiện hành. Job vẫn có tên pages cho dễ đối chiếu với đề.
- URL/baseUrl lấy từ CI_PAGES_URL, không cần điền tên tài khoản mẫu và không cần tắt unique domain.
- Không cần chuyển tệp từ website/: dự án đã nằm ở gốc.

## Minh chứng cần bổ sung sau khi chạy GitLab

- URL repository và commit đã chạy.
- Pipeline cơ bản: ba stage, bốn job; log test-job2 và deploy-prod.
- Job đầu tiên: lời chào và ngày giờ.
- Build thành công và artifacts chứa index.html.
- Pipeline build/deploy thành công; trang Pages mở được.

Không có ảnh hoặc kết quả GitLab giả lập trong bộ bài. Xem KIEM-TRA.md để biết các kiểm tra thực tế tại máy.

## Tài liệu đối chiếu

- https://docs.gitlab.com/ci/yaml/
- https://docs.gitlab.com/user/project/pages/
- https://docusaurus.io/docs/installation

GitLab Self-Managed cũ có thể cần cú pháp Pages tương ứng phiên bản máy chủ. Các job trong examples là cấu hình thay thế để làm từng bước, không tự chạy cùng pipeline mặc định.

## Mô tả các tệp

| Tệp | Chức năng |
| --- | --- |
| `.gitlab-ci.yml` | Pipeline cuối: build Docusaurus, publish Pages |
| `examples/01-basic.yml` | Phần 6.2.1: build, hai test và deploy mô phỏng |
| `examples/02-first-job.yml` | Job đầu tiên: echo và date |
| `examples/03-build.yml` | Build và lưu artifacts |
| `examples/04-audit.yml` | Job SCA mở rộng để ghép vào pipeline |
| `docusaurus.config.js` | Cấu hình website và URL Pages |
| `docs/index.md` | Nội dung lý thuyết và giải thích thực hành |
| `package-lock.json` | Khóa phiên bản dependency cho npm ci |

## Trả lời giải thích kết quả

- Stage xác định thứ tự nhóm công việc. Job trong cùng stage có thể chạy song song khi đủ runner.
- Mỗi job chạy trong môi trường riêng. Artifact chuyển đầu ra build sang job deploy; cache chủ yếu giúp giảm thời gian cài đặt.
- Nếu build thất bại, job Pages không chạy. Pages chỉ xuất bản từ nhánh mặc định.
- npm ci yêu cầu lockfile khớp package.json; không tự cập nhật phiên bản phụ thuộc khi chạy CI.
- Không đặt token vào YAML hoặc README. Các biến nhạy cảm thuộc phần cấu hình bảo mật của nền tảng CI.
- Chạy build thành công chỉ xác nhận website tạo được; không chứng minh ứng dụng không có lỗ hổng.
