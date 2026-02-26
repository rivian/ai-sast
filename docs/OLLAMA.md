# Running AI-SAST with Ollama (Local Open-Source LLM)

Ollama allows you to run AI-SAST completely locally without any cloud dependencies. Your code never leaves your machine, and there are no cloud costs or rate limits.

## Quick Start

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull recommended model
ollama pull qwen2.5-coder:14b

# Configure AI-SAST
export AI_SAST_LLM="ollama"
export OLLAMA_MODEL="qwen2.5-coder:14b"

# Run a scan
python examples/ollama_scan.py
```

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | macOS, Linux, Windows (WSL2) | macOS or Linux |
| **RAM** | 8GB (for 7B models) | 16GB+ (for 14B models) |
| **Disk Space** | 5GB free | 20GB+ free |
| **CPU** | Any modern CPU | Multi-core CPU |
| **GPU** | Not required | NVIDIA/AMD GPU (10x faster) |

---

## Installation Guide

### 1. Install Ollama

**macOS / Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Download from [https://ollama.com/download/windows](https://ollama.com/download/windows)

**Verify Installation:**
```bash
ollama --version
```

### 2. Start Ollama Service

**macOS:**
Ollama starts automatically after installation.

**Linux:**
```bash
# Start service
ollama serve

# Or run in background
nohup ollama serve &
```

**Check if running:**
```bash
curl http://localhost:11434/api/tags
```

### 3. Pull a Model

**Recommended for most users:**
```bash
ollama pull qwen2.5-coder:14b
```

**Other options:**
```bash
# Faster, smaller model (4GB RAM)
ollama pull qwen2.5-coder:7b

# Most accurate (20GB RAM)
ollama pull qwen2.5-coder:32b

# Alternatives
ollama pull codellama:13b
ollama pull llama3.1:8b
ollama pull deepseek-coder:33b
```

**List installed models:**
```bash
ollama list
```

### 4. Install AI-SAST

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/ai-sast.git
cd ai-sast

# Install Python dependencies
pip install -r requirements.txt
```

### 5. Configure AI-SAST for Ollama

```bash
# Set backend to Ollama
export AI_SAST_LLM="ollama"

# Optional: Change model (defaults to qwen2.5-coder:14b)
export OLLAMA_MODEL="qwen2.5-coder:14b"

# Optional: Change Ollama URL (defaults to http://localhost:11434)
export OLLAMA_BASE_URL="http://localhost:11434"
```

### 6. Run Your First Scan

```bash
# Test with example
python examples/ollama_scan.py

# Scan a file
python -m src.core.scanner --file your_file.py

# Scan a directory
python -m src.core.scanner --directory ./your-code
```

---

## Model Selection Guide

| Model | RAM | Speed | Accuracy | Best For |
|-------|-----|-------|----------|----------|
| `qwen2.5-coder:7b` | 4GB | Fast | ⭐⭐⭐⭐ | Quick scans, limited RAM |
| `qwen2.5-coder:14b` | 8GB | Medium | ⭐⭐⭐⭐⭐ | **Recommended default** |
| `qwen2.5-coder:32b` | 20GB | Slow | ⭐⭐⭐⭐⭐ | Maximum accuracy |
| `codellama:13b` | 8GB | Medium | ⭐⭐⭐⭐ | Alternative option |
| `llama3.1:8b` | 5GB | Medium | ⭐⭐⭐⭐ | General purpose |
| `deepseek-coder:33b` | 20GB | Slow | ⭐⭐⭐⭐⭐ | Very capable alternative |

### Recommended Models for Security Scanning

**Best Overall:** `qwen2.5-coder:14b`
- Excellent code understanding
- Good balance of speed and accuracy
- 8GB RAM requirement
- Trained specifically for code analysis

**If you have limited RAM:** `qwen2.5-coder:7b`
- Still very capable
- Only 4GB RAM required
- Faster inference

**If you want maximum accuracy:** `qwen2.5-coder:32b`
- Best detection accuracy
- Requires 20GB RAM
- Slower but most thorough

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AI_SAST_LLM` | Set to `ollama` for local Ollama; `vertex` for Vertex AI | `vertex` |
| `OLLAMA_BASE_URL` | Ollama API endpoint | `http://localhost:11434` |
| `OLLAMA_MODEL` | Model to use | `qwen2.5-coder:14b` |

### Using with GitHub Actions

Ollama requires a running service, so it's primarily for local development. For CI/CD, use Vertex AI:

```yaml
# .github/workflows/pr-scan.yml
env:
  AI_SAST_LLM: "vertex"  # Use Vertex AI in CI/CD
  GOOGLE_CLOUD_PROJECT: ${{ secrets.GOOGLE_CLOUD_PROJECT }}
```

For local development:
```bash
# Local
export AI_SAST_LLM="ollama"
```

---

## Troubleshooting

### "Connection refused"

**Problem:** Cannot connect to Ollama service

**Solution:**
```bash
# Make sure Ollama is running
ollama serve

# Or check status
curl http://localhost:11434/api/tags

# Expected response: {"models":[...]}
```

### "Model not found"

**Problem:** The specified model is not installed

**Solution:**
```bash
# List available models
ollama list

# Pull the model you want
ollama pull qwen2.5-coder:14b

# Verify it's installed
ollama list
```

### "Out of memory"

**Problem:** Not enough RAM for the model

**Solution:**
```bash
# Use a smaller model
ollama pull qwen2.5-coder:7b
export OLLAMA_MODEL="qwen2.5-coder:7b"

# Or close other applications to free memory
# Check memory usage: free -h (Linux) or Activity Monitor (macOS)
```

### Slow performance

**Problem:** Scans are taking too long

**Solutions:**

1. **Check if GPU is being used:**
```bash
ollama ps
# Look for GPU in the output
```

2. **Install GPU drivers:**
```bash
# For NVIDIA GPUs
# Install CUDA toolkit from: https://developer.nvidia.com/cuda-downloads

# For AMD GPUs
# Install ROCm from: https://www.amd.com/en/graphics/servers-solutions-rocm
```

3. **Use a smaller/faster model:**
```bash
ollama pull qwen2.5-coder:7b
export OLLAMA_MODEL="qwen2.5-coder:7b"
```

4. **Close other applications** to free up system resources

### Model downloads slowly

**Problem:** `ollama pull` is very slow

**Solutions:**
- Check your internet connection
- Models are large (7B model ≈ 4GB, 14B model ≈ 8GB, 32B model ≈ 20GB)
- Use a wired connection if possible
- Download during off-peak hours

### Ollama service crashes

**Problem:** Ollama stops unexpectedly

**Solutions:**
```bash
# Check logs
ollama logs

# Restart service
ollama serve

# Check system resources
top  # Linux
Activity Monitor  # macOS

# Make sure you have enough RAM for the model
```

---

## Performance Tips

### 1. Use GPU Acceleration

**NVIDIA GPUs:**
```bash
# Install CUDA toolkit
# Download from: https://developer.nvidia.com/cuda-downloads

# Ollama will automatically detect and use CUDA
ollama ps  # Check if GPU is listed
```

**AMD GPUs:**
```bash
# Install ROCm
# Follow instructions: https://www.amd.com/en/graphics/servers-solutions-rocm

# Ollama will automatically detect and use ROCm
```

**Expected speedup:** 5-10x faster with GPU

### 2. Choose the Right Model Size

- **Fast scans:** Use `qwen2.5-coder:7b`
- **Balanced:** Use `qwen2.5-coder:14b` (recommended)
- **Accuracy:** Use `qwen2.5-coder:32b`

### 3. Optimize System Resources

```bash
# Close unnecessary applications
# Ensure Ollama has enough RAM
# Use SSD for model storage (faster loading)
```

### 4. Keep Models Updated

```bash
# Check for model updates periodically
ollama pull qwen2.5-coder:14b

# Models improve over time
```

### 5. Use Local NVMe/SSD Storage

- Store Ollama models on fast storage
- Default location: `~/.ollama/models`
- Move to SSD if on HDD for faster loading

---

## Switching Between Backends

### Use Vertex AI (Cloud)

```bash
unset AI_SAST_LLM  # Uses default (vertex)
# or
export AI_SAST_LLM="vertex"
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

### Use Ollama (Local)

```bash
export AI_SAST_LLM="ollama"
export OLLAMA_MODEL="qwen2.5-coder:14b"
```

### Per-Command Override

```bash
# Use Vertex AI for this scan only
AI_SAST_LLM="vertex" python -m src.core.scanner --file test.py

# Use Ollama for this scan only
AI_SAST_LLM="ollama" python -m src.core.scanner --file test.py
```

---

## Benefits of Ollama

✅ **100% Free and Open-Source**
- No cloud costs
- No subscription fees
- No API rate limits

✅ **Privacy-First**
- Your code never leaves your machine
- No data sent to third parties
- Perfect for sensitive codebases

✅ **Works Offline**
- No internet required after model download
- Great for air-gapped environments
- Reliable in any network conditions

✅ **Unlimited Usage**
- No rate limits
- Scan as much as you want
- No quotas or throttling

✅ **Fast (with GPU)**
- 5-10x faster with GPU acceleration
- Real-time scanning possible
- No network latency

---

## Limitations of Ollama

❌ **Requires Local Resources**
- Need sufficient RAM (8GB+ recommended)
- Models take disk space (4-20GB each)
- GPU recommended for best performance

❌ **Setup Required**
- Manual installation and configuration
- Model downloads needed
- Service must be running

❌ **Not for CI/CD (yet)**
- GitHub Actions runners don't have Ollama
- Better to use Vertex AI for CI/CD
- Self-hosted runners could work

---

## Advanced Configuration

### Custom Ollama Port

If port 11434 is in use:

```bash
# Start Ollama on custom port
OLLAMA_HOST=127.0.0.1:11435 ollama serve

# Configure AI-SAST
export OLLAMA_BASE_URL="http://localhost:11435"
```

### Remote Ollama Instance

Run Ollama on a separate machine:

```bash
# On server (expose to network)
OLLAMA_HOST=0.0.0.0:11434 ollama serve

# On client
export OLLAMA_BASE_URL="http://your-server-ip:11434"
```

⚠️ **Warning:** Only do this on trusted networks. Ollama has no built-in authentication.

### Model Temperature & Parameters

Models are configured in `src/integrations/ollama.py`:

```python
# Default settings
temperature=0.2  # Lower = more deterministic
max_tokens=None  # No limit
```

To customize, edit the file or modify the `generate()` call.

---

## Getting Help

**Ollama Documentation:** [https://ollama.com/docs](https://ollama.com/docs)

**Ollama GitHub:** [https://github.com/ollama/ollama](https://github.com/ollama/ollama)

**AI-SAST Issues:** [https://github.com/YOUR_USERNAME/ai-sast/issues](https://github.com/YOUR_USERNAME/ai-sast/issues)

**Model Library:** [https://ollama.com/library](https://ollama.com/library)

---

## FAQ

**Q: Can I use Ollama in GitHub Actions?**
A: Not easily. GitHub Actions runners don't have Ollama installed. Use Vertex AI for CI/CD, Ollama for local development.

**Q: Which model is best for security scanning?**
A: `qwen2.5-coder:14b` offers the best balance of speed and accuracy for code security analysis.

**Q: How much RAM do I need?**
A: 8GB minimum for 7B models, 16GB recommended for 14B models, 32GB+ for 32B models.

**Q: Does Ollama support multiple languages?**
A: Yes, models like Qwen2.5-Coder support all major programming languages.

**Q: Can I use multiple models?**
A: Yes, pull multiple models and switch by changing `OLLAMA_MODEL` environment variable.

**Q: Is GPU required?**
A: No, but highly recommended for good performance. CPU-only works but is 5-10x slower.

**Q: Can I use Ollama on Windows?**
A: Yes, download from [ollama.com/download/windows](https://ollama.com/download/windows) or use WSL2.

**Q: How do I update models?**
A: Run `ollama pull <model-name>` again to get the latest version.
