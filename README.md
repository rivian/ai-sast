# AI-SAST - AI-Powered Static Application Security Testing

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![GitHub Actions](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=github-actions)](https://github.com/features/actions)

AI-SAST is an AI-driven static application security testing tool. Run it in **your** repository on **your** runners—PR scan on pull requests, full scan on demand. Your code never runs on ai-sast infrastructure.

## Features

- **Vertex AI (Gemini)** or **Ollama** backends
- **PR scan**: Scans changed files on pull requests; posts findings as PR comments
- **Full scan**: Manual run to scan the entire repository
- **Your runners**: Workflow runs in your repo (e.g. self-hosted); your code stays on your infrastructure
- Multi-language support (Python, JS/TS, Java, Go, Rust, C/C++, and more)
- CVSS scoring, configurable exclusions, optional feedback loop

## Integrate in your repository

1. **Copy the workflow file** into your repo as `.github/workflows/ai-sast.yml`:  
   [`.github/workflows/ai-sast.yml`](.github/workflows/ai-sast.yml)

2. **Add repository secrets** (Settings → Secrets and variables → Actions):  
   `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CREDENTIALS`

The workflow checks out **`rivian/ai-sast`** at runtime. **PR scan** runs on pull requests (when base branch is `main`); **full scan** runs when you click "Run workflow" in the Actions tab.

**Optional:** Set variable `AI_SAST_REPO` (e.g. for a fork); `AI_SAST_BASE_BRANCH` (default `main`); `runs-on: self-hosted` in the workflow for your own runners.

📚 **Full guide:** [docs/INTEGRATION.md](docs/INTEGRATION.md)

## Architecture

![AI-SAST Architecture](docs/images/architecture.png)

1. **Trigger**: Pull request or manual "Run workflow"
2. **Scan**: Code is analyzed by Vertex AI (Gemini) or Ollama
3. **Results**: PR comments and HTML/text report artifacts

📖 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Optional configuration

- **Historical vulnerabilities (highly recommended):** Add Jira context so the LLM sees past vulnerability patterns and improves accuracy. Set `JIRA_SERVER`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_PROJECT_KEY` as repository variables or in the workflow env.
- **Severity filter**: Set variable `AI_SAST_SEVERITY` (e.g. `critical,high`). Default: `critical,high`.
- **Feedback loop**: [docs/FEEDBACK-LOOP.md](docs/FEEDBACK-LOOP.md)

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

## Troubleshooting

- **Auth errors:** Service account needs "Vertex AI User" role; `GOOGLE_CREDENTIALS` must be the full JSON key.
- **No PR comment:** Ensure the PR targets the branch set by `AI_SAST_BASE_BRANCH` (default `main`).
- **Using a fork:** Set repository variable `AI_SAST_REPO` to your `org/ai-sast`.

## Support

- 🐛 [Report bugs](../../issues)
- 💬 [Discussions](../../discussions)
- 📖 [Documentation](docs/)

---

Made with ❤️ by the AI-SAST community
