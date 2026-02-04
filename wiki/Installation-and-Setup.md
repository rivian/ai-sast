# Installation and Setup

Get AI-SAST up and running in minutes with either cloud-based Vertex AI or local Ollama.

## Prerequisites

- **Python 3.8 or higher**
- **Git** (for cloning the repository)
- **Google Cloud account** (for Vertex AI) OR **Ollama** (for local execution)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/ai-sast.git
cd ai-sast
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## Setup Options

Choose your backend:

---

## Option A: Vertex AI (Cloud - Recommended for CI/CD)

### Step 1: Set Up Google Cloud

1. **Create/Select a Google Cloud Project**
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Enable Vertex AI API**
   ```bash
   gcloud services enable aiplatform.googleapis.com
   ```

3. **Create Service Account** (for GitHub Actions)
   ```bash
   gcloud iam service-accounts create ai-sast-scanner \
     --display-name="AI-SAST Scanner"
   
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:ai-sast-scanner@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"
   
   gcloud iam service-accounts keys create credentials.json \
     --iam-account=ai-sast-scanner@YOUR_PROJECT_ID.iam.gserviceaccount.com
   ```

### Step 2: Configure Environment Variables

```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_TOKEN="$(cat credentials.json)"
```

### Step 3: Test the Setup

```bash
python examples/basic_scan.py
```

---

## Option B: Ollama (Local - Free & Private)

### Step 1: Install Ollama

**macOS/Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Download from [ollama.com](https://ollama.com)

### Step 2: Pull a Model

```bash
# Recommended model for security scanning
ollama pull qwen2.5-coder:14b

# Alternative (lighter model)
ollama pull qwen2.5-coder:7b
```

### Step 3: Configure Environment Variables

```bash
export LLM_BACKEND="ollama"
export OLLAMA_MODEL="qwen2.5-coder:14b"
```

### Step 4: Test the Setup

```bash
python examples/ollama_scan.py
```

---

## GitHub Actions Setup

### 1. Add Repository Secrets

Go to your repository: **Settings → Secrets and variables → Actions → Secrets**

Add these secrets:
- `GOOGLE_CLOUD_PROJECT`: Your GCP project ID
- `GOOGLE_CREDENTIALS`: Contents of your `credentials.json` file

### 2. Add Repository Variables (Optional)

Go to: **Settings → Secrets and variables → Actions → Variables**

Add these variables:
- `GEMINI_MODEL`: `gemini-2.0-flash-exp` (or another Gemini model)
- `AI_SAST_SEVERITY`: `critical,high` (or customize)

### 3. Enable Workflows

The workflows are already in `.github/workflows/`:
- `pr-scan.yml` - Scans pull requests
- `full-scan.yml` - Scans entire repository
- `collect-feedback.yml` - Collects developer feedback

They'll run automatically on PRs!

---

## Verify Installation

### Test Local Scan

```bash
# Scan a single file
python -m src.core.scanner --file examples/vulnerable_code.py

# Scan a directory
python -m src.main.full_scan --directory ./src
```

### Test PR Scan (Local)

```bash
# Set required environment variables
export GITHUB_REPOSITORY="owner/repo"
export GITHUB_REF_NAME="feature-branch"

# Run PR scan
python -m src.main.pr_scan
```

---

## Troubleshooting

### "Command not found: python"
Use `python3` instead of `python`:
```bash
python3 -m pip install -r requirements.txt
```

### "Vertex AI API not enabled"
```bash
gcloud services enable aiplatform.googleapis.com
```

### "Model not available" (Vertex AI)
Try a different model:
```bash
export GEMINI_MODEL="gemini-1.5-pro"
```

### "Connection refused" (Ollama)
Make sure Ollama is running:
```bash
ollama serve
```

---

## Next Steps

- [**Quick Start Guide**](Quick-Start-Guide) - Run your first scan
- [**Configuration**](Configuration) - Customize AI-SAST
- [**PR Scanning**](PR-Scanning) - Set up automated PR scans

---

[← Back to Home](Home)
