FROM python:3.11-slim

# Prevent Python bytecode and enable unbuffered output
# Limit multi-threading overhead to stay well within 512MB RAM free tier
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000 \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    TORCH_NUM_THREADS=1

# Install minimal build tools needed for C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1. Install lightweight CPU-only PyTorch first
# This prevents downloading heavy NVIDIA CUDA packages (saving ~2.5GB and hundreds of MBs of RAM)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# 2. Copy requirements and install remaining dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Pre-cache the sentence transformer embedding model during build
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# 4. Copy application source and models
COPY . .

# Ensure data and models directories exist
RUN mkdir -p data models

# Expose default HTTP port
EXPOSE 8000

# Start FastAPI server binding dynamically to Render's $PORT
CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
