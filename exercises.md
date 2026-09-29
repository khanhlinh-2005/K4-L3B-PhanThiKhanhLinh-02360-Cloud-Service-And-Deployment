# Phiếu Phản Ánh — K4 Level 3B, Ngày 12

> **Bài làm cá nhân.**
>
> **Họ và tên:** Phan Thị Khánh Linh
> **Mã học viên:** 02360

---

## Câu 1 — Fail fast (CP1)

Một tình huống cụ thể là khi deploy ứng dụng lên Railway nhưng quên cấu hình `AGENT_API_KEY`. Vì `agent_api_key` không có giá trị mặc định nên ứng dụng sẽ báo lỗi cấu hình và dừng ngay khi khởi động. Nhờ vậy em phát hiện được cấu hình bị thiếu trước khi service nhận request. Nếu để mặc định `"changeme"`, ứng dụng vẫn có thể chạy nhưng API có nguy cơ sử dụng một secret yếu hoặc dùng chung, gây mất an toàn mà khó phát hiện.

---

## Câu 2 — Log cho máy đọc (CP1)

Một dòng log JSON em thu được có dạng:

```json
{"event":"ask_completed","user_id":"test-user","cost":0.0000222,"total_spent":0.0000444}
```

Với dòng log này, em có thể:

1. Lọc và thống kê các request theo `user_id`, `event` hoặc thời gian để theo dõi hoạt động của service.
2. Tính toán và theo dõi chi phí sử dụng thông qua các trường `cost` và `total_spent`.

Nếu chỉ dùng `print("đã trả lời xong")` thì thông tin không có cấu trúc, khó lọc, khó thống kê và khó đưa vào hệ thống monitoring.

---

## Câu 3 — Kích thước image (CP2)

Khi build hai phiên bản, dung lượng image thực tế phụ thuộc vào Dockerfile 1-stage ban đầu và môi trường Docker tại thời điểm build. Bản multi-stage của em nhỏ hơn bản 1-stage.

| Bản         | Dung lượng |
| ----------- | ---------: |
| 1 stage     |     ... MB |
| Multi-stage |     ... MB |

Phần chênh lệch chủ yếu đến từ các thành phần chỉ cần trong quá trình build nhưng không cần khi chạy ứng dụng, chẳng hạn như các file tạm, cache và thành phần build không cần thiết. Multi-stage chỉ đưa các dependency và source cần thiết sang image runtime nên giảm kích thước image.

---

## Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Khi em sửa một ký tự trong `app/main.py` rồi build lại, các layer trước bước `COPY . .` vẫn có thể được Docker sử dụng lại từ cache. Đặc biệt, layer cài dependency bằng `RUN pip install` không cần chạy lại nếu `requirements.txt` không thay đổi.

Nếu đặt `COPY . .` trước `RUN pip install` thì mỗi khi source code thay đổi, layer `COPY` bị thay đổi và các layer phía sau nó, trong đó có `RUN pip install`, có thể phải chạy lại. Điều này làm build chậm hơn.

Vì vậy nên copy `requirements.txt`, cài dependency trước rồi mới copy source code để tận dụng Docker layer cache.

---

## Câu 5 — Vì sao không chạy bằng root (CP2)

Một chuỗi sự kiện có thể xảy ra là: ứng dụng Python có một lỗ hổng → kẻ tấn công khai thác lỗ hổng để thực thi code bên trong container → process bị chiếm quyền có quyền của user đang chạy container → nếu container chạy bằng root thì attacker có quyền rất cao trong container và có thể tiếp tục tìm cách khai thác cấu hình hoặc lỗ hổng của Docker/host.

Lệnh `USER appuser` làm process trong container chạy bằng user thường thay vì root. Vì vậy nếu ứng dụng bị khai thác, attacker cũng chỉ có quyền của `appuser`, giúp giảm mức độ ảnh hưởng và hạn chế quyền truy cập vào các tài nguyên quan trọng.

---

## Câu 6 — Cửa sổ trượt (CP3)

Nếu rate limit 10 request/phút nhưng dùng cách đếm theo phút đồng hồ, người dùng có thể gửi tối đa **20 request trong khoảng 2 giây** nếu thực hiện ngay trước và ngay sau thời điểm chuyển phút.

Ví dụ:

* Từ 12:59:59 đến trước 13:00:00: gửi 10 request.
* Ngay sau 13:00:00: bộ đếm được reset, gửi thêm 10 request.

Như vậy trong khoảng thời gian rất ngắn có thể có 20 request.

Sliding window 60 giây tránh trường hợp này vì nó xét các request thực tế trong 60 giây gần nhất thay vì phụ thuộc vào mốc phút trên đồng hồ.

---

## Câu 7 — Rate limit và cost guard (CP3)

Rate limit và cost guard bảo vệ hai vấn đề khác nhau.

* **Rate limit** giới hạn số lượng request trong một khoảng thời gian, giúp bảo vệ service khỏi quá nhiều request trong thời gian ngắn. Khi vượt giới hạn, API trả về `429 Too Many Requests`.
* **Cost guard** giới hạn tổng chi phí sử dụng theo tháng. Khi chi phí dự kiến vượt ngân sách, API chặn request và trả về `402 Payment Required`.

Ví dụ rate limit có thể cho request đi qua vì người dùng mới gửi vài request trong phút hiện tại, nhưng cost guard vẫn có thể chặn nếu ngân sách tháng của người dùng đã gần hoặc vượt giới hạn.

Ngược lại, người dùng có thể chưa vượt rate limit nhưng một request có chi phí rất lớn khiến tổng chi phí vượt ngân sách, khi đó cost guard phải chặn.

---

## Câu 8 — `/health` khác `/ready` (CP4)

Nếu gộp `/health` và `/ready` thành một endpoint và bắt endpoint đó phải kiểm tra Redis thì khi Redis mất kết nối, diễn biến sẽ là:

1. Redis mất kết nối.
2. Cả 3 container gọi endpoint kiểm tra trạng thái.
3. Endpoint không kết nối được Redis nên cả 3 container trả trạng thái không sẵn sàng, thường là HTTP `503`.
4. Hệ thống orchestration/load balancer có thể hiểu rằng cả 3 container đều không healthy/ready và ngừng gửi traffic đến chúng.
5. Mặc dù ứng dụng vẫn có thể đang chạy, nó bị coi là không phục vụ được chỉ vì dependency Redis tạm thời gặp sự cố.

Tách `/health` và `/ready` giúp phân biệt: `/health` kiểm tra process còn sống, còn `/ready` kiểm tra service đã sẵn sàng phục vụ và có thể kiểm tra Redis.

---

## Câu 9 — Stateless (CP4)

Khi lịch sử hội thoại được lưu trong Redis, nhiều container có thể cùng truy cập một nguồn dữ liệu chung. Vì vậy khi gọi `/ask` nhiều lần với cùng `X-User-Id`, `history_length` vẫn tăng liên tục dù request có thể được xử lý bởi các container khác nhau.

Nếu lịch sử được lưu trong một `dict` Python thì mỗi container sẽ có một bộ nhớ riêng. Khi request chuyển sang container khác, container đó có thể không biết lịch sử đã được lưu ở container trước. Vì vậy `history_length` có thể bị giảm hoặc quay lại từ đầu tùy container xử lý request.

Redis giúp service giữ trạng thái dùng chung và cho phép các instance hoạt động theo hướng stateless.

---

## Câu 10 — Deploy thật (CP5)

Một lỗi em gặp trong quá trình deploy là khi gọi API bằng PowerShell, request `/ask` trả về lỗi **HTTP 422 Unprocessable Entity**.

Em kiểm tra lại log Railway và thấy service đã deploy thành công, Uvicorn đã chạy và endpoint `/health` hoạt động. Vì vậy em xác định lỗi không nằm ở quá trình Docker build hoặc Railway deployment mà nằm ở request gửi lên API.

Nguyên nhân là cách truyền JSON bằng `curl` trong PowerShell khác với cách truyền JSON trong nhiều môi trường shell khác, khiến request body không được FastAPI nhận đúng theo model `AskRequest`.

Em chuyển sang sử dụng `Invoke-RestMethod` và tạo JSON bằng `ConvertTo-Json`. Sau khi thay đổi cách gửi request, `/ask` hoạt động bình thường.
