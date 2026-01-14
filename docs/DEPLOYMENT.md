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

**Using Docker Compose**:

```bash
docker-compose up -d
```

**Or manually**:

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


