# ===================== BUILDER =====================
FROM python:3.11-slim AS builder

WORKDIR /build

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DEFAULT_TIMEOUT=100

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install poetry + export plugin
RUN pip install poetry poetry-plugin-export

COPY pyproject.toml poetry.lock* ./

# Export dependencies
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# 🚨 REMOVE GPU + TORCH deps (CRITICAL FIX)
RUN sed -i '/torch/d' requirements.txt \
 && sed -i '/torchvision/d' requirements.txt \
 && sed -i '/torchaudio/d' requirements.txt \
 && sed -i '/nvidia/d' requirements.txt \
 && sed -i '/triton/d' requirements.txt

# ✅ Install CPU-only torch FIRST
RUN pip install \
    torch torchvision \
    --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
RUN pip install -r requirements.txt


# ===================== RUNTIME =====================
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    libmagic1 \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages only
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app
COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8000"]