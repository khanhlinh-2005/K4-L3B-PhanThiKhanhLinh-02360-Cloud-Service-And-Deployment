# =========================
# Stage 1: Builder
# =========================
FROM python:3.11-slim AS builder

WORKDIR /build

# Copy dependency file trước để tận dụng Docker layer cache
COPY requirements.txt .

# Cài dependency vào thư mục riêng
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# =========================
# Stage 2: Runtime
# =========================
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy Python dependencies từ builder
COPY --from=builder /install /usr/local

# Copy source code sau cùng
COPY app ./app
COPY utils ./utils
COPY requirements.txt .

# Tạo user thường, không chạy container bằng root
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app

USER appuser

# Port mặc định; có thể override bằng biến môi trường PORT
ENV PORT=8000

EXPOSE 8000

# Docker kiểm tra service có thực sự hoạt động hay không
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:' + __import__('os').environ.get('PORT', '8000') + '/health')" || exit 1

# Bind ra toàn bộ network interface của container
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
