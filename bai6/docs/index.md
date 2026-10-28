---
slug: /
title: Bài 6 - Bảo mật với DevSecOps
sidebar_position: 1
---

## Mục tiêu

Tạo pipeline GitLab cơ bản, build trang Docusaurus, lưu artifacts và triển khai GitLab Pages.

## 6.1 Tích hợp bảo mật trong CI/CD

### Thiết kế pipeline an toàn

- Phân quyền tối thiểu, bật MFA cho tài khoản, bảo vệ nhánh mặc định.
- Lưu token trong CI/CD Variables, bật Masked và Protected khi phù hợp. Không commit bí mật.
- Dùng runner cô lập; không cấp quyền đặc biệt nếu job không cần.
- Dùng merge request và duyệt thay đổi cấu hình pipeline.
- Ký và xác minh commit/artifact theo chính sách dự án; lưu log để audit.

### Kiểm thử bảo mật tự động

| Loại | Đối tượng | Ví dụ công cụ |
| --- | --- | --- |
| SAST | Mã nguồn | Semgrep |
| DAST | Ứng dụng đang chạy trong môi trường kiểm thử | OWASP ZAP |
| SCA | Phụ thuộc trực tiếp và gián tiếp | npm audit |
| Secret scanning | Khóa, token trong mã và lịch sử Git | Gitleaks |
| Container scanning | Image và gói hệ điều hành | Trivy |

Security gate phải thất bại khi phát hiện vấn đề vượt ngưỡng đã quy định. False positive cần được xác minh và có ngoại lệ được phê duyệt, có thời hạn. Không dùng `allow_failure: true` cho gate bắt buộc.

### Bảo mật IaC

Rà soát Terraform/Ansible trước khi triển khai bằng Checkov hoặc Trivy config. Hạn chế cổng mở, áp dụng quyền tối thiểu, mã hóa dữ liệu và tránh ghi bí mật vào state hay mã nguồn. Pipeline của bài này chưa tạo hạ tầng, vì vậy chưa có tệp IaC để quét.

## 6.2.1 Pipeline cơ bản

Dùng `examples/01-basic.yml` làm `.gitlab-ci.yml`. Stage build chạy trước, hai job test có thể chạy song song nếu đủ runner, deploy chạy sau khi test thành công. `sleep 20` mô phỏng job dài; lệnh echo ở deploy chỉ là mô phỏng, chưa triển khai ứng dụng.

## 6.2.2 Pipeline Docusaurus

Cấu hình mặc định gồm hai stage:

1. `build-job`: cài đúng dependency trong lockfile bằng `npm ci`, chạy build, lưu thư mục `build/` dưới dạng artifact.
2. `pages`: nhận artifact, chuyển `build` thành `public`, kiểm tra `index.html` và xuất bản trên nhánh mặc định.

`CI_PAGES_URL` được dùng để suy ra `url` và `baseUrl`, hỗ trợ đường dẫn dự án hoặc unique domain mà GitLab cấp.

## Phạm vi bảo mật đã triển khai

Bản mặc định thực hiện bài thực hành build/deploy. Nó chưa tích hợp đủ SAST, DAST, secret scan, ký artifact và kiểm tra IaC. Ví dụ mở rộng `examples/04-audit.yml` bổ sung SCA cho dependency production, không thay thế những kiểm tra còn lại.
