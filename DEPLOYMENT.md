# Phiếu Phản Ánh — K4 Level 3B, Ngày 12

> **Bài làm cá nhân.**
> Trả lời: Phan Thị Khánh Linh — mã học viên: 02360

---

## Thông tin triển khai

* **Platform:** Railway
* **Service:** `production-agent`
* **Public URL:** https://production-agent-production-c168.up.railway.app
* **Repository:** `<LINK_REPOSITORY_CUA_BAN>`
* **Backend:** FastAPI
* **Database/Cache:** Redis
* **Container:** Docker
* **Python runtime:** Python 3.11-slim trong production image

---

## Biến môi trường

Các biến môi trường đã được cấu hình trên Railway:

| Biến môi trường         | Giá trị / trạng thái                                                        |
| ----------------------- | --------------------------------------------------------------------------- |
| `AGENT_API_KEY`         | Đã cấu hình trên Railway, không ghi giá trị secret vào tài liệu             |
| `REDIS_URL`             | Đã cấu hình từ Railway Redis service, không ghi giá trị secret vào tài liệu |
| `RATE_LIMIT_PER_MINUTE` | `10`                                                                        |
| `MONTHLY_BUDGET_USD`    | `10.0`                                                                      |
| `LOG_LEVEL`             | `INFO`                                                                      |
| `PORT`                  | Railway tự cung cấp                                                         |

> **Lưu ý bảo mật:** Không ghi giá trị thực của `AGENT_API_KEY` hoặc `REDIS_URL` vào `DEPLOYMENT.md`, Git repository hoặc tài liệu public.

---

## Câu 1 — Fail fast

Trong `Settings`, `agent_api_key` không có giá trị mặc định nên ứng dụng sẽ báo lỗi ngay khi khởi động nếu biến môi trường bắt buộc này bị thiếu.

Cách này giúp phát hiện lỗi cấu hình ngay từ đầu thay vì để ứng dụng chạy rồi mới lỗi khi có request. Đây là nguyên tắc **fail fast**, giúp giảm thời gian tìm lỗi và tránh triển khai một service có cấu hình không đầy đủ.

---

## Câu 2 — Structured log

Structured log giúp log được ghi dưới dạng dữ liệu có cấu trúc, trong bài là JSON. Ví dụ khi gọi `/ask`, log có thể chứa các trường như `event`, `user_id`, `cost` và `total_spent`.

Từ một dòng log JSON có thể dễ dàng:

* tìm kiếm theo từng trường;
* lọc request của một user;
* thống kê chi phí;
* đưa log vào hệ thống giám sát hoặc phân tích sau này.

Structured log cũng dễ xử lý tự động hơn log dạng câu văn tự do.

---

## Câu 3 — Kích thước Docker image

Dockerfile sử dụng **multi-stage build** và base image `python:3.11-slim` để giảm kích thước image.

Ở stage đầu tiên, dependency được cài vào thư mục `/install`. Stage runtime chỉ copy phần dependency cần thiết cùng source code ứng dụng, thay vì mang toàn bộ môi trường build sang image cuối.

Việc dùng image `slim` và multi-stage build giúp image nhỏ hơn, giảm thời gian build/pull và giảm số thành phần không cần thiết trong production container.

---

## Câu 4 — Docker layer cache

Dockerfile được sắp xếp để copy `requirements.txt` và cài dependency trước khi copy source code.

Ví dụ:

```dockerfile
COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

COPY app ./app

COPY utils ./utils
```

Khi chỉ thay đổi code trong `app` hoặc `utils`, layer cài dependency có thể được Docker sử dụng lại từ cache. Vì vậy không cần cài lại toàn bộ package trong mỗi lần build.

Cách sắp xếp layer này giúp giảm đáng kể thời gian build khi phát triển và deploy nhiều lần.

---

## Câu 5 — Container non-root

Container production không nên chạy bằng `root` vì nếu ứng dụng bị khai thác, quyền của tiến trình trong container sẽ quá cao.

Trong Dockerfile, bài tạo user riêng:

```dockerfile
RUN useradd --create-home --shell /bin/bash appuser
```

sau đó thay đổi quyền thư mục ứng dụng và chạy container bằng user này.

Chạy non-root giúp giảm quyền của ứng dụng và hạn chế tác động nếu xảy ra lỗi bảo mật trong container.

---

## Câu 6 — Sliding window

Rate limiter sử dụng Redis Sorted Set để lưu thời điểm các request của từng user.

Mỗi request được lưu với timestamp. Trước khi kiểm tra giới hạn, hệ thống xóa các request đã nằm ngoài cửa sổ 60 giây. Sau đó đếm số request còn lại.

Nếu số request đã đạt giới hạn `RATE_LIMIT_PER_MINUTE=10` thì request tiếp theo nhận HTTP `429 Too Many Requests`.

Đây là **sliding window** vì cửa sổ 60 giây luôn trượt theo thời điểm request hiện tại, thay vì chia thời gian thành các khoảng cố định.

Redis phù hợp với cách này vì nhiều instance của ứng dụng có thể cùng đọc và ghi bộ đếm thay vì mỗi instance giữ một bộ đếm riêng trong memory.

---

## Câu 7 — Rate limit và Cost Guard

Rate limit và Cost Guard đều bảo vệ hệ thống nhưng kiểm soát hai vấn đề khác nhau.

**Rate limit** kiểm soát số lượng request trong một khoảng thời gian. Trong bài, mỗi user mặc định được tối đa 10 request trong một phút. Khi vượt quá giới hạn, API trả `429`.

**Cost Guard** kiểm soát tổng chi phí sử dụng model trong tháng. Hệ thống lưu số tiền đã sử dụng theo user và tháng. Nếu request mới làm tổng chi phí vượt `MONTHLY_BUDGET_USD`, API trả `402 Payment Required`.

Vì vậy rate limit bảo vệ **tài nguyên và lưu lượng**, còn cost guard bảo vệ **ngân sách**. Một user có thể chưa vượt rate limit nhưng vẫn có thể bị chặn vì đã vượt ngân sách.

---

## Câu 8 — Liveness và Readiness

`/health` và `/ready` phục vụ hai mục đích khác nhau.

**Liveness** thông qua `/health` kiểm tra ứng dụng còn hoạt động hay không. Endpoint này không phụ thuộc vào Redis và có thể trả:

```text
200 OK
```

khi service đang sống.

**Readiness** thông qua `/ready` kiểm tra service đã sẵn sàng nhận traffic hay chưa. Endpoint này kiểm tra kết nối Redis. Nếu Redis không hoạt động, `/ready` trả `503`.

Điều này giúp platform hoặc load balancer không gửi traffic vào một instance đang chạy nhưng chưa có đủ dependency để phục vụ request.

---

## Câu 9 — Stateless scaling

Ứng dụng được thiết kế stateless vì không lưu conversation history trong biến toàn cục hoặc memory của process. Lịch sử hội thoại được lưu trong Redis.

Ví dụ cùng một `X-User-ID` gửi nhiều request thì request sau vẫn đọc được lịch sử từ Redis và `history_length` tăng lên.

Điều này quan trọng khi scale thành nhiều container. Request thứ nhất có thể vào instance A nhưng request tiếp theo có thể vào instance B. Vì state nằm trong Redis dùng chung nên instance B vẫn lấy được dữ liệu.

Nếu lưu state trực tiếp trong Python dictionary của từng process thì mỗi instance sẽ có một bản state riêng, dẫn đến dữ liệu không đồng nhất khi scale.

---

## Câu 10 — Lỗi thực tế khi deploy

Trong quá trình deploy Railway, em gặp một số lỗi thực tế.

Đầu tiên, lệnh `railway` chưa có trên máy nên phải cài Railway CLI trước.

Sau khi deploy thành công, khi kiểm tra `/ask` bằng `curl` trên PowerShell, em gặp HTTP `422` do cách escape JSON không đúng. Lần đầu JSON bị parse sai và lần sau sử dụng `{\"question\":...}` khiến chuỗi JSON bị lỗi. Em chuyển sang dùng `Invoke-RestMethod` kết hợp `ConvertTo-Json`, sau đó request hoạt động đúng.

Một lỗi khác là `pytest tests/test_cp5.py -v` ban đầu không chạy được các test public deployment vì `DEPLOYMENT.md` vẫn còn placeholder và chưa có Public URL thật. Sau khi bổ sung URL Railway, platform và các biến môi trường cần thiết, các test deployment có thể đọc được thông tin cần kiểm tra.

Qua quá trình này, em rút ra rằng khi deploy cần kiểm tra lần lượt **cấu hình → build image → service → environment variables → public URL → health → readiness → authentication → request thực tế**, thay vì chỉ kiểm tra xem container có khởi động hay không.

---

## Thông tin Public Deployment

Service đã được triển khai thành công trên Railway.

**Public URL:**

```text
https://production-agent-production-c168.up.railway.app
```

### Health check

Endpoint:

```text
GET /health
```

Mục đích: kiểm tra service còn hoạt động.

### Readiness check

Endpoint:

```text
GET /ready
```

Mục đích: kiểm tra service và Redis đã sẵn sàng phục vụ request.

### API request

Endpoint:

```text
POST /ask
```

Yêu cầu header xác thực:

```text
X-API-Key: <AGENT_API_KEY>
```

Có thể truyền thêm:

```text
X-User-ID: <user-id>
```

để xác định người dùng và lưu conversation history riêng trong Redis.

---

## Kiểm tra deployment

Quy trình kiểm tra deployment được thực hiện theo thứ tự:

```text
Configuration
      ↓
Docker Build
      ↓
Railway Service
      ↓
Environment Variables
      ↓
Public URL
      ↓
/health
      ↓
/ready
      ↓
Authentication
      ↓
/ask
```

Kết quả deployment:

* Railway service: **đã triển khai**
* Public URL: **HTTPS**
* `/health`: kiểm tra service
* `/ready`: kiểm tra Redis
* `/ask`: yêu cầu API key
* Redis: **đã cấu hình**
* Rate limit: **10 requests/phút/user**
* Monthly budget: **10 USD/user/tháng**

---

## Lưu ý bảo mật

Không lưu các secret sau vào Git hoặc `DEPLOYMENT.md`:

```text
AGENT_API_KEY=<secret thật>
REDIS_URL=<credential thật>
```

Chỉ lưu **tên biến môi trường và trạng thái đã cấu hình**. Secret thực tế được quản lý bằng Environment Variables của Railway.
