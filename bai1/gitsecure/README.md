# GitSecure

Hook phân tích nội dung đã stage bằng git show, quét credential, chạy Bandit và kiểm tra policy giấy phép của dependency trực tiếp trong requirements. Không ghi giá trị bí mật vào log.

Tại gốc kho `sang thu 4`, cài thư viện của bài rồi bật hook:

```powershell
python -m pip install -r bai1/secure-validator-lab/requirements.txt -r bai1/requirements-dev.txt
git config core.hooksPath bai1/.githooks
```

Trên Git Bash: `chmod +x bai1/.githooks/pre-commit`.
Hook yêu cầu Git và Python trong PATH. Log nằm ở gitsecure.log tại gốc kho. Thêm gitsecure.log vào .gitignore trước khi thử.

Quyền world-writable chỉ kiểm tra theo POSIX; Windows dùng ACL nên kiểm tra bit chmod không đủ. Chức năng kiểm tra giấy phép giới hạn các dependency trực tiếp đã pin và policy trong license-policy.json, chưa phải kiểm toán giấy phép toàn bộ cây phụ thuộc. Scanner regex có thể có false positive/false negative.
