# GitHub Action Secrets

The `elastic-agent-review` workflow requires two secrets configured in the repository's **Settings → Secrets and variables → Actions**.

## `ELASTIC_WORKFLOW_KEY`

An API key used to authenticate the HTTP trigger request to the Elastic Workflow.

**Format:** `ApiKey <base64-encoded-id:api_key>`

**How to obtain:**
1. Open Kibana
2. Go to **Stack Management → API Keys**
3. Create a new API key scoped to the workflow trigger endpoint
4. The value to paste into GitHub is the full `ApiKey <...>` string (including the `ApiKey ` prefix)

## `ELASTIC_WORKFLOW_URL`

The full HTTPS URL of the Elastic Workflow HTTP trigger endpoint.

**Format:** `https://<your-elastic-cluster>/api/...`

**How to obtain:**
1. Open Kibana
2. Go to **Workflows** (or **Elastic Agent Builder → Workflows**)
3. Open the PR review workflow
4. Copy the HTTP trigger endpoint URL from the workflow configuration

## Notes

- Secrets are only available to workflows triggered by **internal PRs** (same repo). Forks will not have access — acceptable for this demo (internal use only).
- If either secret is missing, the workflow job will be skipped (not failed), so you won't see red checks before secrets are configured.
- The target Elastic Workflow must be deployed and running before the GitHub Action trigger will produce results. See the MS Build 2026 session bucket 3 (Elastic Workflow side) for setup.
