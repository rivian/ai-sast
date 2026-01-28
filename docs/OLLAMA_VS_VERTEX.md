# Ollama vs Vertex AI: Choosing Your Backend

This guide helps you choose between Ollama and Vertex AI backends for AI-SAST.

## Quick Comparison

| Feature | Ollama (Local) | Vertex AI (Cloud) |
|---------|----------------|-------------------|
| **Cost** | Free | Pay-per-use (~$0.075 per 1M tokens) |
| **Privacy** | 100% local | Code sent to Google Cloud |
| **Speed** | Depends on hardware | Very fast (cloud infrastructure) |
| **Setup** | Simple (ollama pull) | Requires GCP account |
| **Internet** | Not required | Required |
| **Models** | Open-source | Google Gemini (proprietary) |
| **Accuracy** | Good (33B models ~GPT-3.5) | Excellent (Gemini 2.5 Pro) |
| **Resources** | 4-40GB RAM | None (cloud-based) |
| **Rate Limits** | None | Yes (depends on quota) |

## When to Use Ollama

✅ **Best for:**
- Personal projects or small teams
- Privacy-sensitive codebases
- Offline environments
- Cost-conscious deployments
- Learning and experimentation
- Open-source advocates

**Example Use Cases:**
- Internal security tools
- Pre-commit hooks on developer machines
- Air-gapped environments
- Educational purposes
- Avoiding cloud vendor lock-in

## When to Use Vertex AI

✅ **Best for:**
- Production enterprise deployments
- Large teams needing consistent performance
- CI/CD pipelines requiring speed
- Organizations already on Google Cloud
- Need for latest/most capable models

**Example Use Cases:**
- GitHub Actions workflows
- Large-scale repository scanning
- Multi-team organizations
- High-accuracy requirements
- Integration with other GCP services

## Recommended Configurations

### Ollama - Development Machine
```bash
export LLM_BACKEND="ollama"
export OLLAMA_MODEL="qwen2.5-coder:14b"  # Balanced, 8GB RAM
# Good for most use cases
```

### Ollama - Fast Scanning
```bash
export LLM_BACKEND="ollama"
export OLLAMA_MODEL="qwen2.5-coder:7b"  # Fast, 4GB RAM
# Good for quick local scans
```

### Ollama - High Accuracy
```bash
export LLM_BACKEND="ollama"
export OLLAMA_MODEL="qwen2.5-coder:32b"  # 20GB RAM
# Slower but more accurate
```

### Vertex AI - Fast & Cost-Effective
```bash
export LLM_BACKEND="vertex"
export GEMINI_MODEL="gemini-2.0-flash-exp"
# Default, balanced option
```

### Vertex AI - Maximum Accuracy
```bash
export LLM_BACKEND="vertex"
export GEMINI_MODEL="gemini-2.5-pro"
# Most capable, higher cost
```

## Hybrid Approach

You can use both backends in different scenarios:

```bash
# Local development: Use Ollama
export LLM_BACKEND="ollama"
python -m src.main.full_scan --directory ./my-code

# CI/CD: Use Vertex AI (set in GitHub Actions)
# .github/workflows/pr-scan.yml
env:
  LLM_BACKEND: vertex
  GEMINI_MODEL: gemini-2.0-flash-exp
```

## Performance Benchmarks (Approximate)

| Backend | Model | Speed (per file) | Accuracy | Memory |
|---------|-------|------------------|----------|--------|
| Ollama | qwen2.5-coder:7b | 8-20s | ⭐⭐⭐⭐ | 4GB |
| Ollama | qwen2.5-coder:14b | 12-35s | ⭐⭐⭐⭐⭐ | 8GB |
| Ollama | qwen2.5-coder:32b | 25-80s | ⭐⭐⭐⭐⭐ | 20GB |
| Ollama | codellama:13b | 15-45s | ⭐⭐⭐⭐ | 8GB |
| Vertex AI | gemini-2.0-flash-exp | 2-5s | ⭐⭐⭐⭐⭐ | 0 (cloud) |
| Vertex AI | gemini-2.5-pro | 3-8s | ⭐⭐⭐⭐⭐ | 0 (cloud) |

*Note: Ollama speeds depend on your CPU/GPU. With GPU acceleration, Ollama can be 5-10x faster.*

## Cost Comparison (1000 files/month)

**Ollama:**
- Initial: $0 (free download)
- Ongoing: $0
- **Total: $0**

**Vertex AI (gemini-2.0-flash-exp):**
- Typical usage: ~500K tokens per 1000 files
- Cost: ~$0.04 per 1000 files
- **Total: ~$0.04/month**

**Vertex AI (gemini-2.5-pro):**
- Typical usage: ~500K tokens per 1000 files
- Cost: ~$0.25 per 1000 files
- **Total: ~$0.25/month**

## Getting Started with Ollama

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull a model (choose one)
ollama pull qwen2.5-coder:14b       # Recommended for most
ollama pull qwen2.5-coder:7b        # Faster option
ollama pull codellama:13b           # Alternative
ollama pull llama3.1:8b             # General purpose

# 3. Verify
ollama list

# 4. Configure AI-SAST
export LLM_BACKEND="ollama"
export OLLAMA_MODEL="qwen2.5-coder:14b"

# 5. Test
python examples/ollama_scan.py
```

## FAQ

**Q: Can I switch backends without code changes?**
A: Yes! Just change the `LLM_BACKEND` environment variable.

**Q: Which is more accurate?**
A: Vertex AI Gemini 2.5 Pro is currently the most accurate, followed by qwen2.5-coder:32b on Ollama.

**Q: Can I use GPU with Ollama?**
A: Yes! Ollama automatically uses NVIDIA/AMD GPUs if available, significantly improving speed.

**Q: Is Ollama truly private?**
A: Yes, everything runs locally. Your code never leaves your machine.

**Q: What if I hit rate limits with Vertex AI?**
A: Switch to Ollama temporarily, or request quota increase in Google Cloud Console.

## Need Help?

- Ollama docs: https://ollama.com/
- Vertex AI docs: https://cloud.google.com/vertex-ai
- AI-SAST issues: https://github.com/YOUR_ORG/ai-sast/issues
