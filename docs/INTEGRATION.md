# Integrating AI-SAST into Your Repository

Run AI-SAST (PR scan + full scan) **in your repo on your runners**. The workflow checks out your fork of the ai-sast scanner at runtime—no submodule or manual copy. Your code never runs on ai-sast infrastructure.

## Required (4 steps)

### 1. Fork this repository

Fork [rivian/ai-sast](https://github.com/rivian/ai-sast) so the workflow uses your fork. This also helps the project’s visibility (fork count) and lets you customize the scanner.

### 2. Copy the workflow file

- **From this repo:** [`.github/workflows/ai-sast.yml`](../.github/workflows/ai-sast.yml)
- **Save as:** `.github/workflows/ai-sast.yml` in the **repository you want to scan** (not necessarily the fork).

This single file runs PR scan, full scan, and feedback collection (when developers check boxes in PR comments). Feedback is stored in a database and included in the Vertex AI prompt on future scans to improve accuracy.

### 3. Set the AI_SAST_REPO variable

In the repository you want to scan: **Settings → Secrets and variables → Actions → Variables**

| Variable | Value |
|----------|--------|
| `AI_SAST_REPO` | Your fork (e.g. `your-username/ai-sast`) |

The workflow will checkout this repo at runtime. If you skip this, the workflow will fail with instructions to fork and set the variable.

### 4. Add Google secrets

In the same repository: **Settings → Secrets and variables → Actions → Secrets**

| Secret | Description |
|--------|-------------|
| `GOOGLE_CLOUD_PROJECT` | Your GCP project ID |
| `GOOGLE_CREDENTIALS` | Service account JSON (full contents of the key file) |

That’s it—PR scan runs on pull requests (when base branch matches), full scan (manual "Run workflow"), and feedback collection (when a PR comment with the AI-SAST scan is edited and checkboxes are used).

## Optional

- **LLM provider:** Default is **Vertex AI** (Gemini). To use **AWS Bedrock (Claude)** set variable **`AI_SAST_LLM`** = `bedrock`, and set **`AWS_REGION`** (e.g. `us-east-1`), **`BEDROCK_MODEL_ID`**. Add AWS credentials as secrets (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) or use an IAM role on the runner. For local **Ollama**, set **`AI_SAST_LLM`** = `ollama`.
- **Default branch for PR scan:** Add variable **`AI_SAST_BASE_BRANCH`** (e.g. `main`, `master`, `develop`). Default is `main` if unset.
- **Scanner ref:** Add variable **`AI_SAST_REF`** (e.g. `main`, `v1.0`) to pin the ai-sast version. Default is `main`.
- **Update same PR comment:** Set **`AI_SAST_UPDATE_SAME_PR_COMMENT`** = `true` to update the existing AI-SAST comment on each scan run instead of posting a new one (reduces noise when multiple commits trigger multiple scans). Default is `false`.
- **Self-hosted runners:** In the workflow file, set `runs-on: self-hosted` (or your runner label).

## Running scans

- **PR scan**: Open a pull request that targets the branch set by `AI_SAST_BASE_BRANCH` (or `main`). The workflow runs and posts a comment with findings.
- **Full scan**: Actions → **“AI-SAST”** → **“Run workflow”**.

## Troubleshooting

- **“repository not found” or checkout fails:** Ensure `AI_SAST_REPO` is set to your fork (e.g. `your-username/ai-sast`). You must fork the repo first.
- **No PR comment:** Check that the PR targets the branch set by `AI_SAST_BASE_BRANCH` (or `main`). Check the “Run AI-SAST PR Scan” step logs.
- **Feedback not triggering when you check boxes:** The `issue_comment` event runs the workflow from your **default branch** (e.g. `main`). Ensure `ai-sast.yml` is committed and merged to that branch—if the file exists only on a feature branch, feedback collection will not run.
- **Auth errors:** Ensure the service account has the “Vertex AI User” role and that `GOOGLE_CREDENTIALS` is the **full** JSON key (not a path).
