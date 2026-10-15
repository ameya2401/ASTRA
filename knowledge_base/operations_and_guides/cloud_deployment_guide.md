# Cloud Deployment & Production Hosting Guide

> Operating procedures for deploying ASTRA to cloud platforms (Render, Railway, Docker VPS) with persistent HTTPS webhook ingress.

---

## 1. Architecture Overview

Deploying ASTRA to a cloud host replaces local port tunnels (ngrok, smee) with a permanent HTTPS webhook endpoint that runs 24/7:

1. **Ingress:** GitHub delivers pull request events to `https://<your-cloud-domain>/api/v1/github/webhook`.
2. **Container Runtime:** Python 3.11 with Tree-sitter C extensions, PyTorch CPU, and pre-warmed MiniLM/XGBoost models.
3. **Egress:** Non-blocking GitHub REST API comments via `httpx.AsyncClient` back to the origin pull request.

---

## 2. Memory Optimization for Free Tiers (<= 512MB RAM)

By default, installing `sentence-transformers` downloads full GPU PyTorch with 15+ NVIDIA CUDA packages (consuming >2.5GB disk and >450MB idle RAM upon import). On Render's 512MB free tier, this causes an instant `Out of memory (used over 512Mi)` crash.

To keep memory usage under 200MB:
1. **CPU-only PyTorch:** `pip install torch --index-url https://download.pytorch.org/whl/cpu`
2. **Single-threaded inference:**
   - `OMP_NUM_THREADS=1`
   - `MKL_NUM_THREADS=1`
   - `TORCH_NUM_THREADS=1`

---

## 3. Platform Options

### 3.1 Option A: Render (Free Tier Supported)

- **Runtime:** Docker (`ast-triage-core/Dockerfile`)
- **Health Check Endpoint:** `/api/v1/health`
- **Environment Variables:**
  - `GITHUB_TOKEN`: GitHub Personal Access Token or App installation token with `pull_requests:write` and `issues:write`.
  - `GITHUB_WEBHOOK_SECRET`: HMAC-SHA256 secret key matching GitHub webhook configuration.
  - `OMP_NUM_THREADS`: `1`
  - `MKL_NUM_THREADS`: `1`
  - `TORCH_NUM_THREADS`: `1`
- **Port:** Render automatically sets `$PORT`; the Dockerfile dynamically binds to `${PORT:-8000}`.

### 3.2 Option B: Railway

- Connect GitHub repository `ameya2401/ASTRA`.
- Set Root Directory to `/ast-triage-core`.
- Railway automatically detects the Dockerfile, generates a public `.up.railway.app` domain, and provisions SSL.

### 3.3 Option C: Self-Hosted Docker / VPS (AWS, DigitalOcean, Hetzner)

```bash
cd ast-triage-core
docker build -t astra-triage .
docker run -d -p 8000:8000 --env-file .env --name astra astra-triage
```

---

## 4. Webhook Target Configuration

Once deployed, configure the webhook in the target GitHub repository:
- **Payload URL:** `https://<deployed-domain>/api/v1/github/webhook`
- **Content type:** `application/json`
- **Secret:** Must match `GITHUB_WEBHOOK_SECRET` in cloud environment variables.
- **Events:** Pull requests.
