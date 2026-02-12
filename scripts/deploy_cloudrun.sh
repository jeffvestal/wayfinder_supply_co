#!/bin/bash
# deploy_cloudrun.sh - Deploy Wayfinder Supply Co. to Google Cloud Run
#
# Deploys MCP server, backend, and frontend as Cloud Run services,
# then configures Elastic Agent Builder workflows and agents with
# the Cloud Run service URLs.
#
# Prerequisites:
#   - gcloud CLI installed and authenticated
#   - Docker installed (for local builds) OR gcloud builds enabled
#   - .env file with STANDALONE_* Elastic credentials
#   - Vertex AI API enabled on the GCP project

set -e

# Suppress interactive gcloud prompts (e.g., installing beta component)
export CLOUDSDK_CORE_DISABLE_PROMPTS=1

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Defaults
GCP_PROJECT="elastic-customer-eng"
GCP_REGION="us-central1"
BACKEND_SERVICE="wayfinder-demo-backend"
MCP_SERVICE="wayfinder-demo-mcp"
FRONTEND_SERVICE="wayfinder-demo-frontend"
LOAD_DATA=false
DISABLE_IAP=false
API_KEY=""
SKIP_BUILD=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project)
            GCP_PROJECT="$2"
            shift 2
            ;;
        --project=*)
            GCP_PROJECT="${1#*=}"
            shift
            ;;
        --region)
            GCP_REGION="$2"
            shift 2
            ;;
        --region=*)
            GCP_REGION="${1#*=}"
            shift
            ;;
        --wayfinder-api-key)
            API_KEY="$2"
            shift 2
            ;;
        --wayfinder-api-key=*)
            API_KEY="${1#*=}"
            shift
            ;;
        --load-data)
            LOAD_DATA=true
            shift
            ;;
        --disable-iap)
            DISABLE_IAP=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Deploy Wayfinder Supply Co. to Google Cloud Run."
            echo ""
            echo "Options:"
            echo "  --project ID         GCP project (default: elastic-customer-eng)"
            echo "  --region REGION      GCP region (default: us-central1)"
            echo "  --wayfinder-api-key KEY  Shared secret for workflow auth (or from WAYFINDER_API_KEY env)"
            echo "  --load-data          Also load data into Elasticsearch"
            echo "  --disable-iap        Skip IAP setup (IAP is enabled by default for @elastic.co SSO)"
            echo "  --skip-build         Skip building images (use existing)"
            echo "  -h, --help           Show this help"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Load .env if present
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep -E '^(STANDALONE_|WAYFINDER_|JINA_|VERTEX_|GCP_)' | xargs 2>/dev/null) || true
fi

# Resolve API key
if [ -z "$API_KEY" ]; then
    API_KEY="${WAYFINDER_API_KEY:-}"
fi

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACT_REGISTRY="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT}/wayfinder"

echo -e "${BOLD}${CYAN}=============================================="
echo -e "  Wayfinder Supply Co. - Cloud Run Deployment"
echo -e "==============================================${NC}"
echo ""
echo -e "${BLUE}GCP Project:${NC}  $GCP_PROJECT"
echo -e "${BLUE}Region:${NC}       $GCP_REGION"
echo -e "${BLUE}Registry:${NC}     $ARTIFACT_REGISTRY"
if [ -n "$API_KEY" ]; then
    echo -e "${BLUE}API Key:${NC}      ****${API_KEY: -4}"
fi
if [ "$DISABLE_IAP" = false ]; then
    echo -e "${BLUE}IAP:${NC}          Enabled (@elastic.co SSO)"
else
    echo -e "${BLUE}IAP:${NC}          Disabled"
fi
echo ""

# ─── Step 0: Validate prerequisites ────────────────────────────
echo -e "${BOLD}Step 0: Validating prerequisites...${NC}"

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}ERROR: gcloud CLI not found. Install: https://cloud.google.com/sdk/docs/install${NC}"
    exit 1
fi

# Set the project
gcloud config set project "$GCP_PROJECT" --quiet

# Ensure required env vars
if [ -z "$STANDALONE_ELASTICSEARCH_URL" ] || [ -z "$STANDALONE_ELASTICSEARCH_APIKEY" ] || [ -z "$STANDALONE_KIBANA_URL" ]; then
    echo -e "${RED}ERROR: Required Elastic environment variables not set.${NC}"
    echo "Set STANDALONE_ELASTICSEARCH_URL, STANDALONE_ELASTICSEARCH_APIKEY, STANDALONE_KIBANA_URL"
    echo "in .env or export them before running."
    exit 1
fi

# Ensure Artifact Registry repo exists
echo -e "${BLUE}Ensuring Artifact Registry repository exists...${NC}"
if ! gcloud artifacts repositories describe wayfinder --location="$GCP_REGION" --project="$GCP_PROJECT" &>/dev/null; then
    gcloud artifacts repositories create wayfinder \
        --repository-format=docker \
        --location="$GCP_REGION" \
        --project="$GCP_PROJECT" \
        --description="Wayfinder Supply Co. container images" \
        --quiet
    echo -e "${GREEN}   Created Artifact Registry repo: wayfinder${NC}"
else
    echo -e "${GREEN}   Artifact Registry repo exists${NC}"
fi

# Configure Docker auth for Artifact Registry
gcloud auth configure-docker "${GCP_REGION}-docker.pkg.dev" --quiet

echo -e "${GREEN}Prerequisites OK${NC}"
echo ""

# ─── Step 1: Optionally load data ──────────────────────────────
if [ "$LOAD_DATA" = true ]; then
    echo -e "${BOLD}Step 1: Loading data into Elasticsearch...${NC}"
    bash "$REPO_ROOT/scripts/standalone_setup.sh" --data-only
    echo ""
fi

# ─── Step 2: Build and push images ─────────────────────────────
if [ "$SKIP_BUILD" = false ]; then
    echo -e "${BOLD}Step 2: Building and pushing container images...${NC}"
    echo ""

    # Build MCP server (Cloud Run requires linux/amd64)
    echo -e "${BLUE}Building MCP server...${NC}"
    docker build --platform linux/amd64 -t "${ARTIFACT_REGISTRY}/mcp-server:latest" -f "$REPO_ROOT/mcp_server/Dockerfile" "$REPO_ROOT/mcp_server"
    docker push "${ARTIFACT_REGISTRY}/mcp-server:latest"
    echo -e "${GREEN}   Pushed mcp-server${NC}"

    # Build backend
    echo -e "${BLUE}Building backend...${NC}"
    docker build --platform linux/amd64 -t "${ARTIFACT_REGISTRY}/backend:latest" -f "$REPO_ROOT/backend/Dockerfile" "$REPO_ROOT/backend"
    docker push "${ARTIFACT_REGISTRY}/backend:latest"
    echo -e "${GREEN}   Pushed backend${NC}"

    # Frontend is built in step 4 (needs backend URL first)
    echo ""
else
    echo -e "${YELLOW}Skipping image builds (--skip-build)${NC}"
    echo ""
fi

# ─── Step 3: Deploy MCP server ─────────────────────────────────
echo -e "${BOLD}Step 3: Deploying MCP server to Cloud Run...${NC}"

MCP_ENV_FLAG=""
if [ -n "$API_KEY" ]; then
    MCP_ENV_FLAG="--set-env-vars=WAYFINDER_API_KEY=${API_KEY}"
fi

gcloud run deploy "$MCP_SERVICE" \
    --image="${ARTIFACT_REGISTRY}/mcp-server:latest" \
    --region="$GCP_REGION" \
    --platform=managed \
    --allow-unauthenticated \
    $MCP_ENV_FLAG \
    --memory=512Mi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=3 \
    --quiet

MCP_URL=$(gcloud run services describe "$MCP_SERVICE" --region="$GCP_REGION" --format='value(status.url)')
echo -e "${GREEN}   MCP server deployed: ${MCP_URL}${NC}"
echo ""

# ─── Step 4: Deploy backend ────────────────────────────────────
echo -e "${BOLD}Step 4: Deploying backend to Cloud Run...${NC}"

BACKEND_ENV_VARS="STANDALONE_ELASTICSEARCH_URL=${STANDALONE_ELASTICSEARCH_URL}"
BACKEND_ENV_VARS="${BACKEND_ENV_VARS},STANDALONE_ELASTICSEARCH_APIKEY=${STANDALONE_ELASTICSEARCH_APIKEY}"
BACKEND_ENV_VARS="${BACKEND_ENV_VARS},STANDALONE_KIBANA_URL=${STANDALONE_KIBANA_URL}"
BACKEND_ENV_VARS="${BACKEND_ENV_VARS},DISABLE_STATIC_SERVING=true"
if [ -n "$API_KEY" ]; then
    BACKEND_ENV_VARS="${BACKEND_ENV_VARS},WAYFINDER_API_KEY=${API_KEY}"
fi
if [ -n "$JINA_API_KEY" ]; then
    BACKEND_ENV_VARS="${BACKEND_ENV_VARS},JINA_API_KEY=${JINA_API_KEY}"
fi
if [ -n "$VERTEX_PROJECT_ID" ]; then
    BACKEND_ENV_VARS="${BACKEND_ENV_VARS},VERTEX_PROJECT_ID=${VERTEX_PROJECT_ID}"
fi
BACKEND_ENV_VARS="${BACKEND_ENV_VARS},VERTEX_LOCATION=${VERTEX_LOCATION:-us-central1}"
if [ -n "$GCP_SERVICE_ACCOUNT_JSON" ]; then
    BACKEND_ENV_VARS="${BACKEND_ENV_VARS},GCP_SERVICE_ACCOUNT_JSON=${GCP_SERVICE_ACCOUNT_JSON}"
fi

gcloud run deploy "$BACKEND_SERVICE" \
    --image="${ARTIFACT_REGISTRY}/backend:latest" \
    --region="$GCP_REGION" \
    --platform=managed \
    --allow-unauthenticated \
    --set-env-vars="$BACKEND_ENV_VARS" \
    --memory=1Gi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=5 \
    --timeout=300 \
    --quiet

BACKEND_URL=$(gcloud run services describe "$BACKEND_SERVICE" --region="$GCP_REGION" --format='value(status.url)')
echo -e "${GREEN}   Backend deployed: ${BACKEND_URL}${NC}"
echo ""

# ─── Step 5: Build and deploy frontend ─────────────────────────
echo -e "${BOLD}Step 5: Building and deploying frontend to Cloud Run...${NC}"

if [ "$SKIP_BUILD" = false ]; then
    echo -e "${BLUE}Building frontend with VITE_API_URL=${BACKEND_URL}...${NC}"
    FRONTEND_BUILD_ARGS="--build-arg VITE_API_URL=${BACKEND_URL}"
    if [ -n "$API_KEY" ]; then
        FRONTEND_BUILD_ARGS="${FRONTEND_BUILD_ARGS} --build-arg VITE_WAYFINDER_API_KEY=${API_KEY}"
        echo -e "${BLUE}   (with API key baked into bundle)${NC}"
    fi
    docker build \
        --platform linux/amd64 \
        -t "${ARTIFACT_REGISTRY}/frontend:latest" \
        -f "$REPO_ROOT/frontend/Dockerfile.prod" \
        $FRONTEND_BUILD_ARGS \
        "$REPO_ROOT/frontend"
    docker push "${ARTIFACT_REGISTRY}/frontend:latest"
    echo -e "${GREEN}   Pushed frontend${NC}"
fi

FRONTEND_AUTH_FLAG="--allow-unauthenticated"
if [ "$DISABLE_IAP" = false ]; then
    # When IAP is enabled, don't allow unauthenticated access (IAP handles auth)
    FRONTEND_AUTH_FLAG="--no-allow-unauthenticated"
fi

gcloud run deploy "$FRONTEND_SERVICE" \
    --image="${ARTIFACT_REGISTRY}/frontend:latest" \
    --region="$GCP_REGION" \
    --platform=managed \
    $FRONTEND_AUTH_FLAG \
    --memory=256Mi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=3 \
    --quiet

FRONTEND_URL=$(gcloud run services describe "$FRONTEND_SERVICE" --region="$GCP_REGION" --format='value(status.url)')
echo -e "${GREEN}   Frontend deployed: ${FRONTEND_URL}${NC}"
echo ""

# ─── Step 6: Deploy workflows and agents ───────────────────────
echo -e "${BOLD}Step 6: Deploying Elastic workflows and agents...${NC}"

API_KEY_FLAG=""
if [ -n "$API_KEY" ]; then
    API_KEY_FLAG="--wayfinder-api-key $API_KEY"
fi

# Deploy workflows with Cloud Run URLs
python3 scripts/deploy_workflows.py \
    --workflows-dir config/workflows \
    --mcp-url "${MCP_URL}/mcp" \
    --backend-url "${BACKEND_URL}" \
    $API_KEY_FLAG

echo ""

# Create agents with Cloud Run URLs
python3 scripts/create_agents.py \
    --mcp-url "${MCP_URL}/mcp" \
    --backend-url "${BACKEND_URL}" \
    $API_KEY_FLAG

echo ""

# ─── Step 7: Enable IAP (@elastic.co SSO) ────────────────────
if [ "$DISABLE_IAP" = false ]; then
    echo -e "${BOLD}Step 7: Enabling IAP for @elastic.co SSO on frontend...${NC}"

    # Ensure IAP API is enabled
    gcloud services enable iap.googleapis.com --project="$GCP_PROJECT" --quiet

    # Enable IAP directly on the Cloud Run frontend service (no load balancer needed)
    echo -e "${BLUE}   Enabling IAP on ${FRONTEND_SERVICE}...${NC}"
    gcloud beta run services update "$FRONTEND_SERVICE" \
        --region="$GCP_REGION" \
        --iap \
        --quiet

    # Get project number for IAP service agent
    PROJECT_NUMBER=$(gcloud projects describe "$GCP_PROJECT" --format='value(projectNumber)')

    # Ensure the IAP service agent exists
    gcloud beta services identity create --service=iap.googleapis.com --project="$GCP_PROJECT" 2>/dev/null || true

    # Grant invoker role to IAP service agent (so IAP can forward requests to Cloud Run)
    echo -e "${BLUE}   Granting IAP service agent invoker role...${NC}"
    gcloud run services add-iam-policy-binding "$FRONTEND_SERVICE" \
        --region="$GCP_REGION" \
        --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-iap.iam.gserviceaccount.com" \
        --role="roles/run.invoker" \
        --quiet

    # Grant access to @elastic.co domain
    echo -e "${BLUE}   Granting @elastic.co domain access...${NC}"
    gcloud beta iap web add-iam-policy-binding \
        --member='domain:elastic.co' \
        --role='roles/iap.httpsResourceAccessor' \
        --region="$GCP_REGION" \
        --resource-type=cloud-run \
        --service="$FRONTEND_SERVICE" \
        --quiet

    echo -e "${GREEN}   IAP enabled: @elastic.co users can access the frontend via Google SSO${NC}"
    echo ""
else
    echo -e "${YELLOW}Skipping IAP setup (--disable-iap)${NC}"
    echo ""
fi

# ─── Step 8: Summary ───────────────────────────────────────────
echo -e "${BOLD}${CYAN}=============================================="
echo -e "  Deployment Complete!"
echo -e "==============================================${NC}"
echo ""
echo -e "${BOLD}Service URLs:${NC}"
echo -e "  ${GREEN}Frontend:${NC}  ${FRONTEND_URL}"
echo -e "  ${GREEN}Backend:${NC}   ${BACKEND_URL}"
echo -e "  ${GREEN}MCP:${NC}       ${MCP_URL}"
echo ""
echo -e "${BOLD}Elastic Stack:${NC}"
echo -e "  ${BLUE}Elasticsearch:${NC}  ${STANDALONE_ELASTICSEARCH_URL}"
echo -e "  ${BLUE}Kibana:${NC}         ${STANDALONE_KIBANA_URL}"
echo ""
if [ "$DISABLE_IAP" = false ]; then
    echo -e "${BOLD}Authentication:${NC}"
    echo -e "  ${GREEN}IAP:${NC}  Enabled (restricted to @elastic.co Google SSO)"
    echo ""
    echo -e "  ${YELLOW}Note:${NC} IAP uses the native Cloud Run integration (Preview)."
    echo -e "  Manage access: gcloud beta iap web get-iam-policy --region=${GCP_REGION} --resource-type=cloud-run --service=${FRONTEND_SERVICE}"
    echo ""
fi

echo -e "${BOLD}To tear down:${NC}"
echo "  gcloud run services delete ${FRONTEND_SERVICE} --region=${GCP_REGION} --quiet"
echo "  gcloud run services delete ${BACKEND_SERVICE} --region=${GCP_REGION} --quiet"
echo "  gcloud run services delete ${MCP_SERVICE} --region=${GCP_REGION} --quiet"
echo ""
