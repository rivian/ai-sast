# AI-SAST - AI-Powered Static Application Security Testing

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![GitHub Actions](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=github-actions)](https://github.com/features/actions)

AI-SAST is an AI-driven static application security testing tool. Run it in **your** repository on **your** runners—PR scan on pull requests, full scan on demand. Your code never runs on ai-sast infrastructure.

## Features

- **Vertex AI (Gemini)** (default), **AWS Bedrock (Claude Opus)**, or **Ollama** backends
- **PR scan**: Scans changed files on pull requests; posts findings as PR comments
- **Full scan**: Manual run to scan the entire repository
- **Your runners**: Workflow runs in your repo (e.g. self-hosted); your code stays on your infrastructure
- Multi-language support (Python, JS/TS, Java, Go, Rust, C/C++, and more)
- CVSS scoring, configurable exclusions, optional feedback loop

## Architecture

![AI-SAST Architecture](docs/images/architecture.png)

1. **Trigger**: Pull request or manual "Run workflow"
2. **Scan**: Code is analyzed by Vertex AI (Gemini), AWS Bedrock (Claude), or Ollama
3. **Results**: PR comments and HTML/text report artifacts

📖 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Integrate in your repository

1. **Copy the workflow file** into your repo as `.github/workflows/ai-sast.yml`:  
   [`.github/workflows/ai-sast.yml`](.github/workflows/ai-sast.yml)

2. **Add repository secrets** (Settings → Secrets and variables → Actions):  
   `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CREDENTIALS`

The workflow checks out **`rivian/ai-sast`** at runtime. One file runs **PR scan** (on pull requests when base branch is `main`), **full scan** (manual "Run workflow"), and **feedback collection** (when someone edits a PR comment and checks a true/false positive box).

**Optional:** Set variable `AI_SAST_REPO` (e.g. for a fork); `AI_SAST_BASE_BRANCH` (default `main`); `runs-on: self-hosted` in the workflow for your own runners.

📚 **Full guide:** [docs/INTEGRATION.md](docs/INTEGRATION.md)

## Optional configuration

- **LLM provider (default: Vertex):** Set `LLM_PROVIDER=vertex` (default) for Google Vertex AI (Gemini), or `LLM_PROVIDER=bedrock` for AWS Bedrock (Claude Opus). For Bedrock, set `AWS_REGION` (e.g. `us-east-1`) and `BEDROCK_MODEL_ID` (e.g. `anthropic.claude-opus-4-5-20251101-v1:0`); use AWS credentials (e.g. `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` or IAM role).
- **Historical vulnerabilities (highly recommended):** Add Jira context so the LLM sees past vulnerability patterns and improves accuracy. Set `JIRA_SERVER`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_PROJECT_KEY` as repository variables or in the workflow env.
- **Severity filter**: Set variable `AI_SAST_SEVERITY` (e.g. `critical,high`). Default: `critical,high`.

## Example PR comment

When the PR scan finds issues, it posts a comment like this:

```markdown
### 🤖 AI-SAST Security Scan
**2** potential issue(s) found.

> 💡 **Help us improve!** Use the checkboxes below to mark each finding as a true positive (✅) or false positive (❌).

| Severity | Count |
|---|---|
| 🔥 High | 2 |

---

<!-- vuln-id: abc12345 -->
- [ ] ✅ True Positive
- [ ] ❌ False Positive

**ID**: `abc12345`
**Severity**: High
**Issue**: SQL Injection vulnerability in user query
**Location**: `src/api/users.py:42`
**CVSS Vector**: `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N`

<details><summary>📋 Click to see details, risk, and remediation</summary>
**Risk:** Attacker could manipulate SQL queries...
**Fix:** Use parameterized queries...
</details>
```

## Feedback loop

Developers can mark findings as **true positive** (✅) or **false positive** (❌) directly in the PR comment. That feedback is **stored in a database** (SQLite by default, or Databricks) and **included in the prompt sent to Vertex AI** on future scans so the model can improve accuracy (e.g. avoid repeating false positives and pay attention to patterns similar to confirmed vulnerabilities).

**How it works:**
1. **PR scan** posts a comment with checkboxes next to each finding.
2. **Developer** checks one box per finding (True Positive or False Positive).
3. **collect-feedback** workflow runs when the comment is edited and **stores feedback in the database**.
4. **Future scans** load that feedback and **add it to the Vertex AI (Gemini) prompt** as context, so the AI gets more accurate over time.

Feedback collection is included in the same workflow file (see Integrate in your repository). No extra configuration needed for SQLite.

📖 **Full guide:** [docs/FEEDBACK-LOOP.md](docs/FEEDBACK-LOOP.md)

## Troubleshooting

- **Auth errors:** Service account needs "Vertex AI User" role; `GOOGLE_CREDENTIALS` must be the full JSON key.
- **No PR comment:** Ensure the PR targets the branch set by `AI_SAST_BASE_BRANCH` (default `main`).
- **Feedback not triggering:** The feedback job runs from your **default branch** (e.g. `main`). Make sure `ai-sast.yml` is merged to that branch—if it only exists on a feature branch, checking boxes in the PR comment won’t trigger the workflow.
- **Using a fork:** Set repository variable `AI_SAST_REPO` to your `org/ai-sast`.

## Support

- 🐛 [Report bugs](../../issues)
- 💬 [Discussions](../../discussions)
- 📖 [Documentation](docs/)

---

Made with ❤️ by the AI-SAST community
