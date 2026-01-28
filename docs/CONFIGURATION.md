# AI-SAST Configuration Guide

## LLM Backend: Vertex AI vs Ollama

| Feature | Vertex AI (Cloud) | Ollama (Local) |
|---------|-------------------|----------------|
| **Cost** | ~$0.04 per 1000 files | Free |
| **Privacy** | Code sent to Google Cloud | 100% local |
| **Speed** | 2-5s per file | 8-80s (depends on model/hardware) |
| **Setup** | Requires GCP account | Install Ollama + pull model |
| **Accuracy** | ⭐⭐⭐⭐⭐ (Gemini 2.5 Pro) | ⭐⭐⭐⭐⭐ (qwen2.5-coder:32b) |
| **Best For** | GitHub Actions, production | Local dev, privacy-sensitive |

### Quick Start: Vertex AI (Default)

```bash
export LLM_BACKEND="vertex"  # or omit (vertex is default)
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GEMINI_MODEL="gemini-2.0-flash-exp"
```

### Quick Start: Ollama

```bash
# Install and pull model
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5-coder:14b

# Configure
export LLM_BACKEND="ollama"
export OLLAMA_MODEL="qwen2.5-coder:14b"  # optional, this is default
```

**Recommended Models:**
- `qwen2.5-coder:14b` - Best balance (8GB RAM, default)
- `qwen2.5-coder:7b` - Faster (4GB RAM)
- `qwen2.5-coder:32b` - Most accurate (20GB RAM)
- `codellama:13b` - Alternative (8GB RAM)
- `llama3.1:8b` - General purpose (5GB RAM)

---

## PR Comment Configuration

### Severity Filter

Control which findings appear in PR comments:

```bash
# Default (recommended): Only critical and high
export AI_SAST_SEVERITY="critical,high"

# Include medium findings
export AI_SAST_SEVERITY="critical,high,medium"

# Everything
export AI_SAST_SEVERITY="critical,high,medium,low"
```

**In GitHub Actions:** Set as repository variable (`AI_SAST_SEVERITY`)  
**Note:** Full HTML reports always include ALL severities

### PR Comment Format

Every finding includes:
- **Unique ID** (`a7b3c9f2`) for tracking
- **Checkboxes** for feedback:
  - `- [ ] ✅ True Positive`
  - `- [ ] ❌ False Positive`
- **Severity, Issue, Location** with clickable links
- **CVSS Vector** and remediation details

Example:
```markdown
<!-- vuln-id: a7b3c9f2 -->
- [ ] ✅ True Positive
- [ ] ❌ False Positive

**ID**: `a7b3c9f2`
**Severity**: Critical
**Issue**: SQL Injection vulnerability
**Location**: [`src/auth/login.py:45`](...)
```

---

## Feedback Loop System

### How It Works

1. **Scan finds vulnerabilities** → PR comment posted with checkboxes
2. **Developer reviews** → Checks ✅ True Positive or ❌ False Positive
3. **Webhook captures feedback** → Stores in SQLite database
4. **Future scans use feedback** → AI learns from past decisions

### Unique Vulnerability IDs

Each finding has a stable ID based on `file + issue + location`:
- **Same vulnerability** = Same ID across scans
- **Tracks feedback** over time
- **Deduplication** of findings
- **ML learning** from historical data

```python
# ID Generation
vuln_id = sha1(f"{file_path}-{issue}-{location}")[:8]
# Example: "a7b3c9f2"
```

### Database Storage

**SQLite (default):** `~/.ai-sast/scans.db`
- `scan_results` table: Initial findings
- `feedback` table: Developer feedback

**Databricks (enterprise):** See [INTEGRATIONS.md](../INTEGRATIONS.md)

---

## Environment Variables

### Core Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| **LLM Backend** |
| `LLM_BACKEND` | `vertex` or `ollama` | `vertex` |
| **Vertex AI** |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | (required for vertex) |
| `VERTEX_AI_LOCATION` | GCP region | `us-central1` |
| `GEMINI_MODEL` | Model name | `gemini-2.0-flash-exp` |
| **Ollama** |
| `OLLAMA_BASE_URL` | API endpoint | `http://localhost:11434` |
| `OLLAMA_MODEL` | Model name | `qwen2.5-coder:14b` |
| **Scanning** |
| `AI_SAST_SEVERITY` | PR comment severities | `critical,high` |
| `AI_SAST_EXCLUDE_PATHS` | Paths to exclude | (optional) |
| `AI_SAST_DB_PATH` | SQLite database path | `~/.ai-sast/scans.db` |

### GitHub Actions Setup

**Set repository variables:**
1. Go to: Settings → Secrets and variables → Actions → Variables
2. Add variables as needed:
   - `GEMINI_MODEL` (optional)
   - `AI_SAST_SEVERITY` (optional)

**Set secrets:**
- `GOOGLE_CLOUD_PROJECT` - Your GCP project
- `GOOGLE_CREDENTIALS` - Service account JSON

---

## Model Selection

### Vertex AI Models

```bash
# Fast and cost-effective (default)
export GEMINI_MODEL="gemini-2.0-flash-exp"

# Most accurate (higher cost)
export GEMINI_MODEL="gemini-2.5-pro"
```

### Ollama Models

| Model | RAM | Speed | Best For |
|-------|-----|-------|----------|
| `qwen2.5-coder:7b` | 4GB | Fast | Quick scans |
| `qwen2.5-coder:14b` | 8GB | Medium | **Default** |
| `qwen2.5-coder:32b` | 20GB | Slow | Max accuracy |
| `codellama:13b` | 8GB | Medium | Alternative |
| `llama3.1:8b` | 5GB | Medium | General purpose |

**Install:** `ollama pull <model-name>`

---

## Performance Tips

### Vertex AI
- Use `gemini-2.0-flash-exp` for speed
- Request quota increase if hitting rate limits
- Use `--max-workers 1` for full scans to avoid rate limits

### Ollama
- **GPU acceleration**: Install CUDA/ROCm for 5-10x speedup
- **Smaller models**: Use 7B for faster scans
- **More RAM**: Close other apps to free memory
- **SSD storage**: Faster model loading

---

## Best Practices

### Hybrid Approach (Recommended)

```bash
# Local development: Ollama (free, private)
export LLM_BACKEND="ollama"
python -m src.main.pr_scan

# GitHub Actions: Vertex AI (fast, reliable)
# Set in workflow env, not locally
```

### Severity Configuration

**Conservative (Production):**
```bash
AI_SAST_SEVERITY="critical,high"
```

**Thorough (Security-focused):**
```bash
AI_SAST_SEVERITY="critical,high,medium"
```

### Feedback Collection

- ✅ Enable webhook for automatic feedback capture
- ✅ Review false positives regularly
- ✅ Use unique IDs to track recurring issues
- ✅ Export data periodically for analysis

---

## Troubleshooting

### Vertex AI

**429 Rate Limit:**
- Increase wait times between requests
- Use `--max-workers 1`
- Request quota increase in GCP Console

**404 Model Not Found:**
- Check `GEMINI_MODEL` spelling
- Verify model availability in your region
- Ensure Vertex AI API is enabled

### Ollama

**Connection Refused:**
```bash
# Start Ollama service
ollama serve

# Check status
curl http://localhost:11434/api/tags
```

**Model Not Found:**
```bash
# List installed models
ollama list

# Pull required model
ollama pull qwen2.5-coder:14b
```

**Out of Memory:**
```bash
# Use smaller model
export OLLAMA_MODEL="qwen2.5-coder:7b"
```

---

## Summary

**2 files to know:**
1. **This file** - Configuration and setup
2. **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design overview

**Quick decisions:**
- **Use Vertex AI for:** GitHub Actions, production, teams
- **Use Ollama for:** Local dev, privacy, cost-free scanning
- **PR comments:** Default `critical,high` is good for most teams
- **Feedback:** Works automatically with SQLite (no setup needed)

For integration details: See [INTEGRATIONS.md](../INTEGRATIONS.md)
