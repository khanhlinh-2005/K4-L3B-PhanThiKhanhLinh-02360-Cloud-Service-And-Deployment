# K4 — Level 3B, Ngày 12: Hạ Tầng Cloud & Deployment (240 phút)

[![CI/CD](https://github.com/khanhlinh-2005/K4-L3B-PhanThiKhanhLinh-02360-Cloud-Service-And-Deployment/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/khanhlinh-2005/K4-L3B-PhanThiKhanhLinh-02360-Cloud-Service-And-Deployment/actions/workflows/ci-cd.yml)

Đưa một AI agent từ `localhost:8000` lên một địa chỉ công khai mà người khác
gọi được, có bảo mật, có giới hạn chi phí, và không sập khi bạn deploy bản mới.

---

## ⚠️ Bài Làm Cá Nhân

**Đây là bài tập cá nhân. Mỗi học viên nộp một repository của riêng mình.**

Tài liệu chính thức của bài lab:

* [SUBMISSION.md](SUBMISSION.md) — cấu trúc bài nộp, tên repo và nơi nộp
* [RUBRIC.md](RUBRIC.md) — tiêu chí chấm, bằng chứng và điều kiện mất điểm
* [CHECKPOINTS.md](CHECKPOINTS.md) — sản phẩm, kiến thức và cách tự kiểm tra từng checkpoint
* [RULES.md](RULES.md) — quy định làm bài, dùng AI, hợp tác và bảo mật

| Được phép                                              | Không được phép                       |
| ------------------------------------------------------ | ------------------------------------- |
| Đọc tài liệu, Stack Overflow, tra AI để hiểu khái niệm | Sao chép code của học viên khác       |
| Hỏi Lab Coach khi bị kẹt                               | Dùng chung repo, chung commit history |
| Thảo luận **cách tiếp cận** với bạn cùng lớp           | Nhờ người khác làm hộ, kể cả một phần |
| Dùng AI để giải thích lỗi                              | Nộp code mà bạn không giải thích được |

**Cách kiểm tra:** Lab Coach sẽ chọn ngẫu nhiên học viên để hỏi trực tiếp về code trong bài nộp. Không giải thích được phần mình viết → điểm phần đó bị hủy.

**Phát hiện hai bài trùng nhau bất thường (cùng lỗi chính tả, cùng comment, cùng cấu trúc lạ): cả hai bài đều 0 điểm**, không phân biệt ai chép của ai.

---

## 📦 Cách Đặt Tên Repository

Repo nộp bài **bắt buộc** đặt tên theo mẫu:

```text
K4-L3B-DAY12-<HoVaTen>-<MSSV>-<TenBai>
```

**Quy tắc viết:**

* Họ tên **viết liền, không dấu**, chữ cái đầu mỗi từ viết hoa
* Ngăn cách các phần bằng dấu gạch ngang `-`
* Không khoảng trắng
* `TenBai` của lab này là `CloudServicesAndDeployment`

**Ví dụ:**

| Học viên                        | Tên repo                                                             |
| ------------------------------- | -------------------------------------------------------------------- |
| L3B202600280 — Nguyễn Văn An    | `K4-L3B-DAY12-NguyenVanAn-L3B202600280-CloudServicesAndDeployment`   |
| L3B202601111 — Trần Thị Bích Hà | `K4-L3B-DAY12-TranThiBichHa-L3B202601111-CloudServicesAndDeployment` |

**Sai tên repo = trừ 5 điểm.**

### Tạo repo và bắt đầu làm

```bash
# 1. Fork repo lab về và đổi tên theo cú pháp bên trên

# 2. Clone repo lab về máy
git clone <URL repo bạn đã fork>

cd K4-L3B-DAY12-NguyenVanAn-L3B202600280-CloudServicesAndDeployment

# 3. Commit và Push khi hoàn thiện bài lab
git add .
git commit -m "Checkpoint 0"
git push origin main
```

> Commit sau mỗi checkpoint. Lịch sử commit cho thấy bạn tự làm — một commit duy nhất vào phút chót là dấu hiệu đáng ngờ.

---

## Mục Tiêu

Sau buổi lab này, bạn sẽ:

* Tách toàn bộ cấu hình ra khỏi code theo 12-Factor và biết vì sao secret không được có giá trị mặc định
* Viết Dockerfile multi-stage, chạy container bằng user thường, image dưới 500MB
* Bảo vệ API bằng API key, sliding-window rate limit và cost guard theo tháng
* Phân biệt liveness/readiness probe, xử lý SIGTERM để deploy không rớt request
* Thiết kế service stateless để scale ngang được
* Deploy lên cloud và có một địa chỉ công khai hoạt động thật

---

## Lịch Trình & Checkpoint

| Thời gian từ lúc bắt đầu | Nội dung                                              | Checkpoint                                               | Điểm |
| ------------------------ | ----------------------------------------------------- | -------------------------------------------------------- | ---- |
| Start +0–20 phút         | Setup môi trường, tạo repo đúng tên                   | **CP0 tại Start +20 phút:** `pytest tests/ -v` chạy được | —    |
| Start +20–60 phút        | **Block 1** — 12-Factor Config, Health, Logging       | **CP1:** `pytest tests/test_cp1.py -v`                   | 15   |
| Start +60–105 phút       | **Block 2** — Docker: multi-stage, bảo mật image      | **CP2:** `pytest tests/test_cp2.py -v`                   | 15   |
| Start +105–115 phút      | ☕ Giải lao                                            | —                                                        | —    |
| Start +115–160 phút      | **Block 3** — API Security                            | **CP3:** `pytest tests/test_cp3.py -v`                   | 20   |
| Start +160–200 phút      | **Block 4** — Scaling & Reliability                   | **CP4:** `pytest tests/test_cp4.py -v`                   | 20   |
| Start +200–230 phút      | **Block 5** — Deploy lên cloud                        | **CP5:** `pytest tests/test_cp5.py -v`                   | 15   |
| Start +230–240 phút      | Hoàn thiện `exercises.md`, `python grade.py`, nộp bài | —                                                        | 15   |
| —                        | **BONUS** — CI/CD với GitHub Actions                  | `pytest tests/test_bonus_cicd.py -v`                     | +10  |

### Bonus CI/CD

Workflow được đặt tại:

```text
.github/workflows/ci-cd.yml
```

Workflow thực hiện:

```text
Push / Pull Request
        ↓
Install dependencies
        ↓
Run tests
        ↓
Build Docker image
        ↓
Nếu tất cả PASS
        ↓
Push vào main?
   ┌────┴────┐
   │         │
  Có       Không
   │         │
   ↓         ↓
Deploy     Không deploy
```

---

## Cài Đặt

### Yêu cầu

* Python 3.11+
* Docker & Docker Compose
* Git + tài khoản GitHub
* Tài khoản Railway hoặc Render

Không cần API key của OpenAI hoặc các bên cung cấp API khác: lab dùng **mock LLM** chạy offline.

### Môi trường ảo & thư viện

**Windows PowerShell:**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### File cấu hình

```powershell
copy .env.example .env
```

Tạo API key:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

`.env` đã nằm trong `.gitignore` — **không commit file này**.

### Redis

```powershell
docker compose up -d redis
```

Có thể dùng:

```text
REDIS_URL=fake://
```

để chạy Redis giả trong RAM cho CP1/CP3/CP4.

---

## Cấu Trúc Thư Mục

```text
K4-L3B-DAY12-<HoVaTen>-<MSSV>-CloudServicesAndDeployment/

├── README.md
├── LAB_GUIDE.md
├── exercises.md
├── DEPLOYMENT.md
├── grade.py
├── app/
│   ├── config.py
│   ├── logging_utils.py
│   ├── main.py
│   ├── auth.py
│   ├── rate_limiter.py
│   ├── cost_guard.py
│   ├── store.py
│   └── lifecycle.py
├── utils/
│   └── mock_llm.py
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── railway.toml
├── render.yaml
├── nginx/
│   └── nginx.conf
├── screenshots/
├── .github/
│   └── workflows/
│       └── ci-cd.yml
└── tests/
    ├── test_cp1.py
    ├── test_cp2.py
    ├── test_cp3.py
    ├── test_cp4.py
    ├── test_cp5.py
    ├── test_bonus_cicd.py
    └── conftest.py
```

---

## Chạy Kiểm Thử

```powershell
pytest tests/test_cp1.py -v
pytest tests/ -v
pytest tests/ -v -m "not docker"
```

Kiểm tra Bonus:

```powershell
pytest tests/test_bonus_cicd.py -v
```

Kết quả mục tiêu:

```text
13 passed
```

---

## Chấm Điểm Tự Động

```powershell
python grade.py
```

| Tiêu chí                                 | Cách chấm                  | Điểm    |
| ---------------------------------------- | -------------------------- | ------- |
| CP1 — 12-Factor Config, Health & Logging | `tests/test_cp1.py`        | 15      |
| CP2 — Docker: multi-stage, bảo mật image | `tests/test_cp2.py`        | 15      |
| CP3 — API Security                       | `tests/test_cp3.py`        | 20      |
| CP4 — Scaling & Reliability              | `tests/test_cp4.py`        | 20      |
| CP5 — Cloud Deployment                   | `tests/test_cp5.py`        | 15      |
| `exercises.md` — 10 câu phản ánh         | Đếm số câu đã trả lời      | 15      |
| **Tổng phần bắt buộc**                   |                            | **100** |
| BONUS — CI/CD với GitHub Actions         | `tests/test_bonus_cicd.py` | **+10** |

Tổng điểm cuối cùng không vượt quá 100.

Kiểm tra phần bắt buộc:

```powershell
python grade.py --no-bonus
```

---

## Hướng Dẫn Nộp Bài

```powershell
python grade.py

git status --porcelain

git add -A
git commit -m "Hoàn thành lab Day 12"
git push origin main
```

**Không commit `.env` hoặc API key thật.**

---

## Danh Sách Kiểm Tra Trước Khi Nộp

* [ ] Repo đúng tên `K4-L3B-DAY12-<HoVaTen>-<MSSV>-CloudServicesAndDeployment`
* [ ] `pytest tests/ -v` đã chạy
* [ ] `python grade.py` đã chạy
* [ ] `exercises.md` đủ 10 câu
* [ ] `DEPLOYMENT.md` có Public URL thật
* [ ] Không có API key thật trong repository
* [ ] `.env` không nằm trong Git
* [ ] Không còn `NotImplementedError` trong `app/`
* [ ] Có commit ở nhiều mốc thời gian
* [ ] **Bonus:** `.github/workflows/ci-cd.yml` chạy xanh
* [ ] **Bonus:** README có badge CI/CD
