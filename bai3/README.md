# Bài 3: Bảo mật mạng máy tính

Thực hiện theo `lab-03.pdf`: SecureChat, NetRecon và báo cáo thao tác. Chạy thử bằng socket thật trên `127.0.0.1`; các cổng được cấp động trong kiểm thử để tránh trùng dịch vụ.

## 1. Chuẩn bị

Mở PowerShell trong thư mục kho mã:

```powershell
cd "C:\Users\bunng\Downloads\sang thu 4"
python -m venv bai3/.venv
bai3/.venv/Scripts/Activate.ps1
python -m pip install -r bai3/requirements.txt
```

Python 3.12 trở lên. Nếu PowerShell chặn kích hoạt, dùng trực tiếp `bai3/.venv/Scripts/python.exe` thay cho `python` trong các lệnh dưới.

## 2. SecureChat: tạo chứng chỉ

```powershell
cd bai3/secure-chat
python make_certs.py
python client.py --generate-key
```

`make_certs.py` tạo CA riêng, chứng chỉ server có SAN `localhost`/`127.0.0.1`, chứng chỉ client riêng cho `alice`, `bob`, `carol`. Đây là cách tạo chứng chỉ bằng thư viện cryptography, thay cho yêu cầu cài OpenSSL hệ thống của slide. Có thể nhấp chạy `make-certs.bat` trên Windows. Không chạy lại vào thư mục chứng chỉ đã tồn tại.

`room.key` là khóa AES 256 bit dùng riêng giữa các client của phòng. Server không đọc hoặc nhận khóa này. Trong bài chạy trên một máy, các client đọc cùng tệp; khi triển khai nhiều máy cần chuyển khóa cho đúng người bằng kênh riêng. Từng phòng nên dùng khóa riêng.

## 3. Chạy server và hai client

Mở ba cửa sổ PowerShell, kích hoạt môi trường và vào `bai3/secure-chat` ở mỗi cửa sổ.

**Cửa sổ 1:**

```powershell
python server.py
```

**Cửa sổ 2:**

```powershell
python client.py --user alice --room lobby
```

**Cửa sổ 3:**

```powershell
python client.py --user bob --room lobby
```

Gõ tin nhắn ở Alice, đọc ở Bob, rồi trả lời. Dùng `/join ten_phong` để chuyển phòng, `/quit` để thoát. Client kiểm tra CA và hostname; server bắt buộc client certificate. Danh tính lấy từ CN trong chứng chỉ, không tin username do client tự gửi.

Tin nhắn được mã hóa AES-GCM tại client, kèm room/sender làm authenticated data. Server chuyển ciphertext đến thành viên cùng phòng. Mỗi frame có tiền tố độ dài và giới hạn 64 KiB; có khóa đồng bộ quản lý kết nối, phòng và thao tác gửi.

## 4. NetRecon: chạy dịch vụ mẫu do mình quản lý

Từ thư mục gốc kho mã, mở cửa sổ PowerShell riêng:

```powershell
python bai3/tools/serve_demo.py
```

Lệnh mở HTTP banner tại `127.0.0.1:8080`, UDP echo tại `127.0.0.1:9999`, giao diện tại `http://127.0.0.1:5000`.

## 5. NetRecon CLI

```powershell
cd bai3/netrecon
python cli.py --target 127.0.0.1 --ports 8080,8443 --mode all
python cli.py --target 127.0.0.1 --ports 9999 --protocol udp --mode scan
python cli.py --target 127.0.0.1 --ports 8080 --email-preview report.eml
```

`--mode` nhận `scan`, `service`, `banner`, `map`, `vuln`, `all`. `--rate-limit 10` giới hạn 10 probe/giây; tối đa 128 cổng mỗi lần. Có parser dải cổng như `8000-8010`.

TCP dùng connect scan. UDP chỉ kết luận `open` khi nhận phản hồi; im lặng là `open|filtered`. Firewall trên Windows có thể làm cổng không mở trả `filtered/unknown`. Chế độ quét ẩn mình trong mô tả đề không được triển khai; bản này dùng probe thông thường, không giả mạo hoặc né giám sát.

Whitelist mặc định `127.0.0.0/8`; blacklist ưu tiên hơn whitelist trong `filter_utils.py`. Nhập IP dạng số để tránh DNS rebinding. Không chạy các IP ngoài phạm vi thực hành. NetworkMapper chỉ mô tả host được chọn và các endpoint đã xác nhận mở, không thu thập ARP toàn mạng như mã mẫu.

Muốn nhận diện phiên bản bằng Nmap, cài từ trang chính thức [nmap.org](https://nmap.org/download.html), thêm Nmap vào PATH, rồi chạy:

```powershell
python cli.py --target 127.0.0.1 --ports 8080 --mode service --nmap
```

Lệnh gọi `nmap -sT -sV --version-light` với thời gian và tốc độ giới hạn. Khi không dùng Nmap, nhãn service chỉ là gợi ý theo số cổng; banner lấy từ kết nối thật. Mục vuln đưa ra điểm cần kiểm tra cấu hình, không gán CVE chỉ vì cổng đang mở.

## 6. NetRecon giao diện web

Giữ `serve_demo.py` đang chạy. Truy cập `http://127.0.0.1:5000`, nhập:

| Trường | Giá trị |
|---|---|
| Target IP | `127.0.0.1` |
| Ports | `8080,8443` |
| Protocol | `TCP` |
| Mode | `all` |
| Probes / giây | `10` |

Nhấn **Scan**, xem bảng cổng và báo cáo JSON. Thử lại UDP với cổng `9999`. Thử `192.0.2.1` để quan sát whitelist từ chối trước khi mở kết nối. Nhấn **Tải email báo cáo (.eml)** để tải bản email xem trước.

## 7. Email và nhật ký

Bản thực hành kiểm tra việc tạo email `.eml`; chưa gửi thư thật qua Gmail. Tệp `.env.example` cung cấp tên biến cấu hình SMTP. Nếu tự gửi sau này, sao chép thành `.env`, điền tài khoản/app password của bạn và dùng tùy chọn `--send-email dia_chi_nhan`. Không ghi mật khẩu trong mã hoặc đưa `.env` lên Git.

Hoạt động quét được ghi vào `netrecon.log` có timestamp. Private key, `certs/`, `room.key`, `.env`, log runtime và email cá nhân được loại khỏi Git.

## 8. Chạy toàn bộ kiểm chứng

Từ thư mục gốc kho mã:

```powershell
python bai3/tools/demo.py
```

Lần chạy trên Windows đã đạt **44/44 kiểm tra**, bao gồm TLS 1.3, trao đổi Alice/Bob, phân phòng, sai khóa, replay, sửa ciphertext, sai hostname, sai CA, thiếu client certificate, TCP/UDP thật, rate limit, whitelist/blacklist, Flask và email preview. Kết quả JSON ở `docs/evidence/verification.json`. Không dùng mock socket cho trao đổi mạng.

## 9. Đưa bài lên GitHub

```powershell
git add bai3 .github/workflows/bai3-tests.yml
git commit -m "Add lab03 SecureChat and NetRecon"
git push origin main
```

Mở **Actions → Bài 3 - SecureChat and NetRecon** để xem kiểm chứng trên Ubuntu. Ảnh minh chứng và liên kết lần chạy sẽ được bổ sung sau khi workflow hoàn tất.
