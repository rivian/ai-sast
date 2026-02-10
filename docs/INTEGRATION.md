# Integrating AI-SAST into Your Repository

Run AI-SAST (PR scan + full scan) **in your repo on your runners**. The workflow checks out the ai-sast scanner at runtime—no submodule or manual copy. Your code never runs on ai-sast infrastructure.

## Required (2 steps)

### 1. Copy the workflow file

- **From this repo:** [`.github/workflows/ai-sast.yml`](../.github/workflows/ai-sast.yml)
- **Save as:** `.github/workflows/ai-sast.yml` in **your** repository.

This single file runs PR scan, full scan, and feedback collection (when developers check boxes in PR comments). Feedback is stored in a database and included in the Vertex AI prompt on future scans to improve accuracy.

### 2. Add Google secrets

In your repository: **Settings → Secrets and variables → Actions → Secrets**

| Secret | Description |
|--------|-------------|
| `GOOGLE_CLOUD_PROJECT` | Your GCP project ID |
| `GOOGLE_CREDENTIALS` | Service account JSON (full contents of the key file) |

The workflow checks out **`rivian/ai-sast`** by default. That’s it—PR scan runs on pull requests (when base branch matches), full scan (manual "Run workflow"), and feedback collection (when a PR comment with the AI-SAST scan is edited and checkboxes are used).

## Optional

- **Using a fork:** Set repository variable **`AI_SAST_REPO`** (e.g. `your-org/ai-sast`) to checkout your fork instead of `rivian/ai-sast`.
- **Default branch for PR scan:** Add variable **`AI_SAST_BASE_BRANCH`** (e.g. `main`, `master`, `develop`). Default is `main` if unset.
- **Scanner ref:** Add variable **`AI_SAST_REF`** (e.g. `main`, `v1.0`) to pin the ai-sast version. Default is `main`.
- **Self-hosted runners:** In the workflow file, set `runs-on: self-hosted` (or your runner label).

## Running scans

- **PR scan**: Open a pull request that targets the branch set by `AI_SAST_BASE_BRANCH` (or `main`). The workflow runs and posts a comment with findings.
- **Full scan**: Actions → **“AI-SAST”** → **“Run workflow”**.

## Troubleshooting

- **“repository not found” or checkout fails:** You may be using a fork; set `AI_SAST_REPO` to your `org/ai-sast`.
- **No PR comment:** Check that the PR targets the branch set by `AI_SAST_BASE_BRANCH` (or `main`). Check the “Run AI-SAST PR Scan” step logs.
- **Feedback not triggering when you check boxes:** The `issue_comment` event runs the workflow from your **default branch** (e.g. `main`). Ensure `ai-sast.yml` is committed and merged to that branch—if the file exists only on a feature branch, feedback collection will not run.
- **Auth errors:** Ensure the service account has the “Vertex AI User” role and that `GOOGLE_CREDENTIALS` is the **full** JSON key (not a path).
