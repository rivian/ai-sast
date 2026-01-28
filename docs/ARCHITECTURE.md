# AI-SAST Architecture

## Overview

AI-SAST is an AI-powered SAST tool that scans code for vulnerabilities using either:
- **Vertex AI** (Google Gemini) - Cloud-based
- **Ollama** (open-source models) - Local

## High-Level Flow

```
┌─────────────┐
│   GitHub    │
│  PR / Push  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   GitHub    │
│   Actions   │
└──────┬──────┘
       │
       ▼
┌─────────────┐      ┌──────────────┐
│  AI-SAST    │─────→│ Vertex AI /  │
│   Scanner   │      │    Ollama    │
└──────┬──────┘      └──────────────┘
       │
       ├──→ PR Comment (Critical/High findings)
       ├──→ HTML Report (All findings)
       └──→ SQLite DB (Scan results + feedback)
```

## Core Components

### 1. Scanner (`src/core/scanner.py`)
- Scans code for vulnerabilities
- Supports both Vertex AI and Ollama backends
- Applies exclusion rules and file filters
- Generates structured vulnerability reports

### 2. Report Generator (`src/core/report.py`)
- Creates HTML reports (all severities)
- Creates markdown for PR comments (filtered by severity)
- Generates unique IDs for each finding
- Includes feedback checkboxes

### 3. Scan Modes

**PR Scan (`src/main/pr_scan.py`):**
- Scans only changed files
- Posts findings as PR comment
- Fast (< 1 minute for typical PRs)

**Full Scan (`src/main/full_scan.py`):**
- Scans entire repository
- Manually triggered
- Generates comprehensive report

### 4. Feedback Loop

```
Developer checks box → Webhook captures → Store in SQLite → Future scans use context
```

**Components:**
- **Webhook** (`webhook/main.py`): Captures PR comment edits
- **Database** (`src/integrations/scan_database.py`): Stores results + feedback
- **Context retrieval**: Scanner includes past feedback in AI prompts

## Key Features

### Unique Vulnerability IDs
Each finding gets a stable ID: `sha1(file+issue+location)[:8]`
- Tracks same vulnerability across scans
- Enables feedback history
- Prevents duplicate reports

### Severity Filtering
- **PR comments**: Only configured severities (default: `critical,high`)
- **HTML reports**: Always include all severities
- **Configurable**: Via `AI_SAST_SEVERITY` env var

### Smart Context
Scanner retrieves:
- Past scan results for the repository
- Developer feedback (true/false positives)
- Jira tickets (optional)
- Includes in AI prompt for better accuracy

## Data Storage

### SQLite (Default)
**Location:** `~/.ai-sast/scans.db`

**Tables:**
- `scan_results`: Initial findings (with vuln_id)
- `feedback`: Developer feedback (true/false positive)

**No setup required** - works automatically!

### Databricks (Optional)
For enterprise multi-team deployments. See [INTEGRATIONS.md](../INTEGRATIONS.md).

## GitHub Actions Integration

### Workflows

1. **`.github/workflows/pr-scan.yml`**
   - Triggers on PR to main/dev
   - Scans changed files
   - Posts PR comment
   - Uploads artifacts

2. **`.github/workflows/full-scan.yml`**
   - Manually triggered (`workflow_dispatch`)
   - Scans entire repository
   - Uploads comprehensive report

3. **`.github/workflows/gitleaks.yml`**
   - Secret detection on push
   - Runs in parallel with AI-SAST

### Required Secrets

**For Vertex AI:**
- `GOOGLE_CLOUD_PROJECT`: GCP project ID
- `GOOGLE_CREDENTIALS`: Service account JSON

**For Ollama:**
- None (runs locally, not in GitHub Actions)

## LLM Backend Selection

### Vertex AI (Default in GitHub Actions)
```yaml
env:
  LLM_BACKEND: vertex  # or omit (default)
  GEMINI_MODEL: gemini-2.0-flash-exp
```

### Ollama (For Local Development)
```bash
export LLM_BACKEND="ollama"
export OLLAMA_MODEL="qwen2.5-coder:14b"
```

## Security & Privacy

### Vertex AI
- Code sent to Google Cloud
- Encrypted in transit and at rest
- Processed in specified region
- Not used for Google model training

### Ollama
- 100% local processing
- Code never leaves your machine
- Full control over data
- Open-source models

## Performance

### Typical Scan Times

| Scan Type | Files | Vertex AI | Ollama (14B) |
|-----------|-------|-----------|--------------|
| PR Scan | 1-5 | 10-30s | 1-3 min |
| PR Scan | 10-20 | 30-60s | 3-7 min |
| Full Scan | 100 | 5-10 min | 15-45 min |

**Note:** Ollama times vary with hardware (faster with GPU).

### Rate Limiting

**Vertex AI:**
- Subject to GCP quotas
- Mitigated with exponential backoff
- Use `--max-workers 1` if needed

**Ollama:**
- No rate limits
- Limited by local hardware
- Scale by adding more RAM/GPU

## Extension Points

### Custom Prompts
```bash
export AI_SAST_CUSTOM_PROMPT="Focus on OWASP Top 10"
```

### File Exclusions
```bash
export AI_SAST_EXCLUDE_PATHS="dist,build,vendor"
```

### Supported Languages
Configured in `ai-sast-extensions.txt`:
- Python, JavaScript/TypeScript, Java, C/C++, Go, Rust
- PHP, Ruby, C#, Kotlin, Swift, Scala
- SQL, Shell, Lua, Perl, R
- And more...

## Integrations

### Built-in
- **SQLite**: Default storage (no setup)
- **GitHub Actions**: PR comments and workflows

### Optional
- **Databricks**: Enterprise feedback storage
- **Jira**: Import known vulnerability patterns
- **Slack/Teams/Discord**: Webhook notifications
- **Vector**: Log aggregation

See [INTEGRATIONS.md](../INTEGRATIONS.md) for setup details.

## Development

### Project Structure
```
ai-sast/
├── src/
│   ├── core/           # Scanner, vertex client, report generator
│   ├── integrations/   # Ollama, database, jira, notifications
│   └── main/           # Entry points (pr_scan, full_scan)
├── .github/workflows/  # GitHub Actions
├── webhook/            # Feedback webhook listener
├── examples/           # Usage examples
└── docs/              # This file + CONFIGURATION.md
```

### Key Files
- `src/core/scanner.py` - Main scanning engine
- `src/core/report.py` - Report generation
- `src/core/config.py` - Configuration
- `src/integrations/ollama.py` - Ollama client
- `src/integrations/scan_database.py` - SQLite storage

## Summary

**Core workflow:**
1. GitHub triggers scan on PR/push
2. Scanner analyzes code with AI (Vertex or Ollama)
3. Findings posted as PR comment (filtered by severity)
4. Full report uploaded as artifact
5. Developer provides feedback via checkboxes
6. Webhook captures feedback → stores in database
7. Future scans use feedback for improved accuracy

**Two deployment options:**
- **Cloud (Vertex AI)**: Fast, scalable, production-ready
- **Local (Ollama)**: Private, free, self-hosted

**Minimal maintenance:**
- SQLite database auto-creates
- No external services required (except LLM)
- Optional integrations for enterprise needs

For configuration details, see [CONFIGURATION.md](CONFIGURATION.md).
