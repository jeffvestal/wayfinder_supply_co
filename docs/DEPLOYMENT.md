# Deployment Guide

## Quick Start

### 1. Generate Sample Data

```bash
# Generate products (without AI)
python scripts/generate_sample_data.py

# Or generate with AI (requires Google Cloud credentials)
python scripts/generate_products.py --config config/product_generation.yaml
```

### 2. Set Up Elasticsearch

```bash
# Set environment variables
export ELASTICSEARCH_URL="http://kubernetes-vm:30920"
export KIBANA_URL="http://kubernetes-vm:30001"
export ELASTICSEARCH_APIKEY="your-api-key"

# Create indices
python scripts/setup_elastic.py

# Seed products
python scripts/seed_products.py --products generated_products/products.json

# Seed clickstream data
python scripts/seed_clickstream.py
```

### 3. Deploy Workflows

```bash
# Deploy all workflows
python scripts/deploy_workflows.py --workflows-dir config/workflows
```

### 4. Create Agents

```bash
# Create agents and register tools
python scripts/create_agents.py
```

### 5. Start Services

**Recommended: Use the local demo launcher** (handles ngrok tunnels automatically):

```bash
# First run (load data + start everything):
./scripts/start_local.sh --load-data

# Subsequent runs (just start services + tunnel):
./scripts/start_local.sh
```

This script:
1. Starts Docker Compose services
2. Waits for health checks
3. Launches ngrok tunnels so Elastic Cloud workflows can reach local MCP/backend
4. Redeploys workflows and agents with the ngrok tunnel URLs
5. Keeps ngrok alive (Ctrl+C to stop)

**Or manually with Docker Compose**:

```bash
docker-compose up -d
```

> **Note:** If your Elastic cluster is on Elastic Cloud, workflows that call the MCP
> server or backend (e.g., `check_trip_safety`, `get_customer_profile`, `ground_conditions`)
> will fail without ngrok tunnels. The `start_local.sh` script handles this automatically.

**Or without Docker**:

```bash
# Start MCP server
cd mcp_server
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

# Start backend (in another terminal)
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

# Start frontend (in another terminal)
cd frontend
npm install
npm run dev
```

### 6. Validate Setup

```bash
python scripts/validate_setup.py
```

### ngrok Tunnel Setup (for Elastic Cloud)

When using Elastic Cloud, workflows execute HTTP calls from the cloud and cannot reach
`localhost`. ngrok creates public tunnels to your local services.

**Prerequisites:**

```bash
# Install ngrok
brew install ngrok

# Authenticate (free tier works fine)
ngrok config add-authtoken <your-token>
```

**Automatic (recommended):**

The `start_local.sh` script detects `config/ngrok.yml` and starts tunnels automatically.
The default config tunnels both MCP (port 8001) and backend (port 8000).

**Manual tunnel setup:**

```bash
# Single tunnel (MCP only - sufficient for check_trip_safety and get_customer_profile):
ngrok http 8001

# Then redeploy workflows with the tunnel URL:
python scripts/deploy_workflows.py --mcp-url "https://<your-id>.ngrok-free.app/mcp"
python scripts/create_agents.py --mcp-url "https://<your-id>.ngrok-free.app/mcp"

# For ground_conditions workflow (needs backend), add --backend-url:
python scripts/deploy_workflows.py \
  --mcp-url "https://<mcp-tunnel>.ngrok-free.app/mcp" \
  --backend-url "https://<backend-tunnel>.ngrok-free.app"
```

**Multi-tunnel config** (`config/ngrok.yml`):

```yaml
version: "2"
tunnels:
  mcp:
    addr: 8001
    proto: http
  backend:
    addr: 8000
    proto: http
```

```bash
ngrok start --config config/ngrok.yml --all
```

## Cloud Deployment (GCP Cloud Run)

Deploy the full Wayfinder Supply Co. stack to Google Cloud Run for a persistent,
publicly accessible demo with optional @elastic.co SSO protection.

### Architecture

- **Frontend**: React build served by nginx on Cloud Run
- **Backend**: FastAPI on Cloud Run (connects to Elastic Cloud + Vertex AI)
- **MCP Server**: Persona/CRM service on Cloud Run
- **Weather**: Google Search Grounding via Vertex AI (replaces MCP weather)
- **Auth**: Google IAP for UI access, API key for workflow calls

### Prerequisites

```bash
# Install gcloud CLI
# https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  aiplatform.googleapis.com \
  --project=elastic-customer-eng
```

Required environment variables (in `.env`):

```bash
STANDALONE_ELASTICSEARCH_URL=https://your-cluster.es.cloud:443
STANDALONE_ELASTICSEARCH_APIKEY=your-api-key
STANDALONE_KIBANA_URL=https://your-cluster.kb.cloud:443
WAYFINDER_API_KEY=your-shared-secret        # protects backend/MCP from public access
JINA_API_KEY=your-jina-key                  # optional, for vision features
VERTEX_PROJECT_ID=elastic-customer-eng      # optional, for Google Grounding
```

### One-Command Deploy

```bash
./scripts/deploy_cloudrun.sh --wayfinder-api-key <your-secret>
```

This script:

1. Validates prerequisites (gcloud, project access, env vars)
2. Creates Artifact Registry repository (if needed)
3. Builds and pushes Docker images for MCP, backend, and frontend
4. Deploys all three services to Cloud Run
5. Deploys Elastic workflows with Cloud Run URLs and API key
6. Creates Agent Builder agents with the new workflow IDs
7. Enables IAP on the frontend for @elastic.co SSO (automatic)
8. Prints all service URLs

### Options

```
Usage: ./scripts/deploy_cloudrun.sh [OPTIONS]

Options:
  --project ID         GCP project (default: elastic-customer-eng)
  --region REGION      GCP region (default: us-central1)
  --wayfinder-api-key KEY  Shared secret for workflow auth (or from WAYFINDER_API_KEY env)
  --load-data          Also load data into Elasticsearch
  --disable-iap        Skip IAP setup (IAP is enabled by default for @elastic.co SSO)
  --skip-build         Skip building images (use existing in registry)
  -h, --help           Show help
```

### Redeploying After Code Changes

```bash
# Rebuild and redeploy everything:
./scripts/deploy_cloudrun.sh --wayfinder-api-key <key>

# Skip image builds (just update workflows/agents):
./scripts/deploy_cloudrun.sh --wayfinder-api-key <key> --skip-build
```

### IAP Setup (@elastic.co SSO)

IAP is **enabled automatically** by the deploy script using Cloud Run's native IAP
integration (no load balancer required). This protects the `run.app` URL directly.

The deploy script:

1. Enables the IAP API on the project
2. Enables IAP on the frontend Cloud Run service (`gcloud beta run services update --iap`)
3. Creates the IAP service agent and grants it `roles/run.invoker`
4. Grants `domain:elastic.co` the `roles/iap.httpsResourceAccessor` role

After deployment, any @elastic.co user can access the frontend via their Google account.
Non-@elastic.co users will be denied access.

**Managing access:**

```bash
# View current IAP policy
gcloud beta iap web get-iam-policy \
  --region=us-central1 \
  --resource-type=cloud-run \
  --service=wayfinder-demo-frontend

# Add a specific user
gcloud beta iap web add-iam-policy-binding \
  --member='user:someone@elastic.co' \
  --role='roles/iap.httpsResourceAccessor' \
  --region=us-central1 \
  --resource-type=cloud-run \
  --service=wayfinder-demo-frontend

# Disable IAP on an existing service
gcloud beta run services update wayfinder-demo-frontend \
  --region=us-central1 \
  --no-iap
```

**Skipping IAP:** Use `--disable-iap` to deploy without IAP (e.g., for testing).

**Note:** This uses Cloud Run's native IAP integration, which is in Preview.
It requires the GCP project to be within a Google Cloud organization.

### API Key Authentication

When `WAYFINDER_API_KEY` is set:

- **Backend and MCP server** reject requests without a matching `X-Api-Key` header
- **Workflows** include the key automatically (injected by the deploy script)
- **Health endpoints** (`/health`) are always unauthenticated
- When the env var is **not** set, auth is completely skipped (local dev mode)

### Tearing Down

```bash
gcloud run services delete wayfinder-demo-frontend --region=us-central1 --quiet
gcloud run services delete wayfinder-demo-backend --region=us-central1 --quiet
gcloud run services delete wayfinder-demo-mcp --region=us-central1 --quiet
```

---

## Instruqt Deployment

### Prerequisites

- Instruqt account with access to Elastic images
- GitHub repository with workshop assets

### Setup Steps

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Initial workshop setup"
   git push origin main
   ```

2. **Update Setup Scripts**
   - Update GitHub repo URL in `instruqt/track_scripts/setup-kubernetes-vm`
   - Update GitHub repo URL in `instruqt/track_scripts/setup-host-1`

3. **Upload to Instruqt**
   - Create new track in Instruqt
   - Upload `instruqt/track.yml`
   - Upload `instruqt/config.yml`
   - Upload `instruqt/track_scripts/`

4. **Configure Secrets**
   - Add required secrets in Instruqt dashboard:
     - `SA_LLM_PROXY_BEARER_TOKEN`
     - `GCSKEY_ELASTIC_SA`
     - `ELASTICSEARCH_APIKEY` (auto-generated)

5. **Test Track**
   - Launch test environment
   - Verify all services start correctly
   - Run validation script

## Production Considerations

### Security

- Use environment variables for all secrets
- Enable HTTPS for all services
- Implement rate limiting on APIs
- Use API keys with minimal required permissions

### Performance

- Use connection pooling for Elasticsearch
- Implement caching for product data
- Use CDN for static assets
- Monitor agent response times

### Monitoring

- Set up logging for all services
- Monitor Elasticsearch cluster health
- Track agent execution metrics
- Monitor MCP server response times

### Scaling

- Use load balancer for backend services
- Scale MCP server horizontally
- Use Elasticsearch cluster for high availability
- Implement queue system for agent requests

## Environment Variables

### Backend

```bash
ELASTICSEARCH_URL=http://kubernetes-vm:30920
KIBANA_URL=http://kubernetes-vm:30001
ELASTICSEARCH_APIKEY=your-api-key
```

### MCP Server

```bash
MCP_SERVER_PORT=8001
```

### Frontend

```bash
VITE_API_URL=http://localhost:8000
```

### Product Generation

```bash
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
GOOGLE_API_KEY=your-api-key  # For Gemini
```

## Troubleshooting

### Services Won't Start

- Check Docker is running: `docker ps`
- Verify ports are not in use: `lsof -i :8000,8001,8002`
- Check logs: `docker-compose logs`

### Elasticsearch Connection Issues

- Verify network connectivity
- Check API key permissions
- Ensure Elasticsearch is accessible from backend

### Agent Builder Not Working

- Verify workflows are deployed
- Check agent tools are registered
- Ensure LLM connector is configured
- Review agent execution logs

### MCP Server Errors

- Check MCP server logs
- Verify CRM data file exists
- Test MCP endpoints directly: `curl http://host-1:8002/health`

## Support

For issues or questions:
- Check logs in `/var/log/` (Instruqt) or `docker-compose logs` (local)
- Review [WORKSHOP_GUIDE.md](WORKSHOP_GUIDE.md)
- Consult Elastic documentation


