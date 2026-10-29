# TalentScope — IT / Data Job Market Analysis

Ứng dụng web **Python Flask + SQLite**, tổ chức theo **MVC**:

- **Model:** `models/job_model.py` — schema, truy vấn, lọc, xử lý dữ liệu và các phép thống kê.
- **Controller:** `controllers/job_controller.py` — routes, API và upload CSV.
- **View:** `templates/dashboard.html` + `static/` — giao diện responsive và biểu đồ Chart.js.
- **Database:** `data/jobs.db` — SQLite, khởi tạo tự động.

## Khởi chạy

Yêu cầu Python 3.10+.

```bash
cd job_market_analysis
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python seed.py
python app.py
```

macOS / Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python seed.py
python app.py
```

Mở `http://127.0.0.1:5000` trên trình duyệt.

**Lưu ý:** `seed.py` tạo 200 bản tin **giả lập** (gắn nhãn công ty Demo) chỉ để kiểm thử. Không được diễn giải như số liệu tuyển dụng hiện tại từ LinkedIn/VietnamWorks. Muốn phân tích dữ liệu thực, nhập CSV thực đã thu thập hợp lệ. Có thể xóa `data/jobs.db` để làm trống dữ liệu, sau đó chạy lại `python app.py` mà không chạy seed.

## CSV đầu vào

Mỗi dòng là một tin tuyển dụng. Xem `static/sample_jobs.csv` để biết định dạng.

| Cột | Ý nghĩa |
|---|---|
| external_id | ID duy nhất, có thể để trống (ứng dụng tạo hash từ các trường) |
| title | Tiêu đề tuyển dụng |
| role | `Data Analyst`, `IT Risk`, `Business Analyst`, `Software Development`, hoặc `Cyber Security` |
| level | `Intern`, `Fresher`, `Junior`, hoặc `Senior` |
| city | Thành phố / khu vực đã chuẩn hóa |
| salary_min | Lương thấp nhất, **triệu VND/tháng**, số thập phân với dấu `.` |
| salary_max | Lương cao nhất, **triệu VND/tháng**; có thể rỗng |
| skills | Kỹ năng phân tách bằng `;` hoặc `\|` |
| company | Công ty |
| source | Ví dụ `LinkedIn`, `VietnamWorks` |
| source_url | Link tin gốc, tùy chọn |
| posted_date | Ngày đăng, `YYYY-MM-DD` |

Tất cả các cột trừ `external_id` và `source_url` đều phải tồn tại; có thể để trống `salary_min`, `salary_max` và `skills`. Giới hạn file 5 MB và 10,000 dòng mỗi lần nhập. Dữ liệu trùng `external_id` sẽ bỏ qua. Lỗi dữ liệu sẽ rollback toàn bộ lượt nhập.

**Lưu ý nguồn dữ liệu:** Ứng dụng không tích hợp crawler. Việc thu thập LinkedIn/VietnamWorks cần tuân thủ điều khoản nền tảng, quyền truy cập và các quy định bảo vệ dữ liệu. Có thể xuất dữ liệu từ nguồn được cấp phép, chuẩn hóa và nhập CSV.

## Phương pháp phân tích

- Top 5 kỹ năng: `COUNT(job)` theo kỹ năng; cùng một kỹ năng trong một tin chỉ đếm một lần.
- Lương theo cấp độ: trung bình của midpoint `(salary_min + salary_max) / 2` trên các tin có công bố lương; nếu chỉ một biên thì dùng biên hiện có (ước lượng), loại bỏ tin không công bố lương. Đơn vị triệu VND/tháng.
- Địa điểm: số tin theo `city` trong tập đang lọc, **không tương đương số doanh nghiệp hay số vị trí trống thực tế**.
- Bộ lọc áp dụng đồng thời theo vai trò, cấp độ, thành phố và nguồn.
- API: `GET /api/summary`, `GET /api/jobs` (hỗ trợ query params `role`, `level`, `city`, `source`).

## Hạn chế

1. Dữ liệu mẫu không đại diện thị trường thật; số liệu chỉ dùng trình diễn tính năng.
2. Tin lương rỗng có thể gây thiên lệch chọn mẫu; không thể so sánh chắc chắn nếu lượng mẫu thấp.
3. Nếu thu thập từ hai nền tảng, cần nhận dạng đăng trùng xuyên nguồn (hiện ứng dụng chỉ khử trùng theo `external_id`).
4. `Intern/Fresher/Junior/Senior` do dữ liệu đầu vào quy định; cần tiêu chí gắn nhãn thống nhất trước khi so sánh.
5. Mức lương không bao gồm phụ cấp/thưởng và chưa xử lý quy đổi ngoại tệ, gross/net, hoặc kỳ trả lương. Chuẩn hóa trước khi nhập.
6. Chỉ dành cho học tập hoặc môi trường nội bộ. Để triển khai công khai cần xác thực, CSRF protection, giới hạn truy cập, ghi log và kiểm tra dữ liệu đầu vào bổ sung. Mã CDN cần internet để hiển thị Chart.js.
