# Bài 1 - Cơ sở lập trình bảo mật, kiểm tra đầu vào

Bài làm theo lab-01.pdf. Dùng kho GitHub hiện tại theo yêu cầu, không tạo kho MSSV riêng.

## 1. SecureValidator

```powershell
cd "C:\Users\bunng\Downloads\sang thu 4\bai1\secure-validator-lab"
python -m pip install -r requirements.txt
python -m unittest discover tests -v
python app.py
```

Mở http://127.0.0.1:5000/. Nhập user@example.com, https://8.8.8.8/, report.pdf, chuỗi SQL `' OR 1=1 --` và HTML `<script>alert(1)</script>`. Thử lại URL http://127.0.0.1 và tên tệp ../secret.txt để thấy bị từ chối.

Bộ kiểm thử hiện có 17 test method, bao gồm nhiều subtest hợp lệ và độc hại. Hàm URL không tải nội dung. DNS được kiểm tra tất cả địa chỉ trả về; ứng dụng thực hiện HTTP thật vẫn phải kiểm soát kết nối/redirect để tránh DNS rebinding. Không coi blacklist SQL là cách chống SQL injection: phải dùng truy vấn có tham số. HTML được escape theo ngữ cảnh văn bản, không dùng Jinja safe.

## 2. GitSecure pre-commit

Từ gốc kho:

```powershell
python -m pip install -r bai1/requirements-dev.txt
python -m unittest discover -s bai1/gitsecure/tests -v
python bai1/tools/hook_demo.py
```

Script dùng kho Git tạm riêng: stage dữ liệu credential giả, thử git commit (bị hook chặn), sửa sang biến môi trường rồi commit lại (thành công). Không đưa bad.py có credential giả vào lịch sử kho chính. Kết quả thật lưu tại docs/evidence/hook-demo.json.

Để bật hook cho kho này, xem gitsecure/README.md. Chưa tự thay core.hooksPath của kho chính vì kho còn các bài khác. Hook phân tích snapshot đã stage, chạy Bandit, kiểm tra quyền POSIX và policy giấy phép dependency trực tiếp. Trên Windows, demo thay shebang trong kho tạm bằng đường dẫn Python đang chạy để tránh phụ thuộc env.exe; logic hook không đổi.

## 3. SecureLogger và API

```powershell
cd "C:\Users\bunng\Downloads\sang thu 4\bai1\secure_logger_lab"
python -m pip install -r requirements.txt
python -m unittest discover tests -v
python app.py
```

API chạy cổng 5001 để không trùng app phần trước. Trong Postman chọn POST http://127.0.0.1:5001/validate, Body > raw > JSON:

```json
{"email":"user@example.com","url":"https://8.8.8.8/","filename":"report.pdf","sql":"' OR 1=1 --","html":"<script>alert(1)</script>"}
```

Từ gốc kho, có thể chạy demo API thực bằng Flask test client:

```powershell
python bai1/tools/logger_demo.py
```

Demo gửi request POST qua Flask, đọc log JSON đã che email/token, kiểm tra HMAC trước và sau sửa log, tạo hai archive gzip và xác minh archive. Kết quả lưu tại docs/evidence/logger-demo.json. Bộ test logger có 6 method; GitSecure có 7 method.

Log thực nằm trong logs/ và được gitignore. HMAC cần khóa riêng bảo vệ ngoài log. Nếu không đặt LOG_INTEGRITY_KEY, chương trình tạo khóa ngẫu nhiên trong logs/.integrity.key chỉ cho demo cục bộ. HMAC không ngăn xóa cả phần cuối log lẫn signature tương ứng nếu không có checkpoint tin cậy bên ngoài. Bản này dành cho một tiến trình; triển khai nhiều worker cần dịch vụ ghi log tập trung. Sidecar có đuôi .sig là chuỗi HMAC, không phải chữ ký số bất đối xứng.

## 4. Deploy Render

Dùng New > Web Service, chọn Public Git Repository và URL kho hiện tại. Chọn branch main, runtime Python, Root Directory `bai1/secure-validator-lab`, Build Command `pip install -r requirements.txt`, Start Command `gunicorn --bind 0.0.0.0:$PORT --workers 1 app:app`, Instance Type Free. Kiểm tra URL được Render cấp và thử dữ liệu trên giao diện.

Cấu hình Blueprint ở bai1/render.yaml có rootDir phù hợp kho nhiều bài. Khi tạo Blueprint, đặt Blueprint Path là bai1/render.yaml. Không xóa dịch vụ đang chạy chỉ để tạo lại minh chứng; có thể đối chiếu YAML và lần triển khai có sẵn.

## Điều chỉnh so với mẫu

- URL chặn IP nội bộ, loopback, link-local, userinfo và cổng ngoài policy.
- Tên tệp chặn encoding, đường dẫn Windows và tên thiết bị.
- Không bật Flask debug.
- Hook kiểm tra nội dung đã stage thay cho đọc bản chưa stage; Bandit lỗi sẽ chặn commit.
- Logger dùng HMAC và xác minh thật, xoay cả log cùng sidecar, che PII trong cấu trúc lồng nhau.
- Quyền POSIX không tương đương Windows ACL; kiểm tra giấy phép chưa bao phủ phụ thuộc gián tiếp.

## Tài liệu

- https://render.com/docs/deploy-flask
- https://render.com/docs/blueprint-spec
- Đề lab-01.pdf, các phần 1.2, 1.4 và 1.6.
