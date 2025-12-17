# Tool Cheat Sheet

Quick reference for creating Agent Builder tools.

## Tool Types

### 1. Workflow Tool

Wraps an Elastic Workflow:

```json
{
  "id": "tool-workflow-get-customer-profile",
  "type": "workflow",
  "description": "Retrieve customer profile including purchase history and loyalty tier",
  "configuration": {
    "workflow_id": "<workflow-id>"
  }
}
```

### 2. ES|QL Tool

Executes ES|QL queries directly:

```json
{
  "id": "tool-esql-get-user-affinity",
  "type": "esql",
  "description": "Get top gear preference tags from user browsing behavior",
  "configuration": {
    "query": "FROM user-clickstream | WHERE meta_tags IS NOT NULL | STATS count = COUNT(*) BY meta_tags | SORT count DESC | LIMIT 5",
    "params": {}
  }
}
```

### 3. Index Search Tool

Searches an Elasticsearch index:

```json
{
  "id": "tool-search-product-search",
  "type": "index_search",
  "description": "Search the product catalog for gear recommendations",
  "configuration": {
    "pattern": "product-catalog"
  }
}
```

## Create Tool via API

```bash
curl -X POST "$KIBANA_URL/api/agent_builder/tools" \
  -H "Authorization: ApiKey $ES_APIKEY" \
  -H "Content-Type: application/json" \
  -H "kbn-xsrf: true" \
  -H "x-elastic-internal-origin: kibana" \
  -d '{
    "id": "tool-workflow-example",
    "type": "workflow",
    "description": "Tool description here",
    "configuration": {
      "workflow_id": "<workflow-id>"
    }
  }'
```

## Get Tool ID

```bash
# Get workflow ID first
WORKFLOW_ID=$(curl -s -X GET "$KIBANA_URL/api/workflows" \
  -H "Authorization: ApiKey $ES_APIKEY" \
  -H "kbn-xsrf: true" \
  -H "x-elastic-internal-origin: kibana" \
  | jq -r '.data[] | select(.name=="workflow_name") | .id')
```

## List All Tools

```bash
curl -s -X GET "$KIBANA_URL/api/agent_builder/tools" \
  -H "Authorization: ApiKey $ES_APIKEY" \
  -H "kbn-xsrf: true" \
  -H "x-elastic-internal-origin: kibana" \
  | jq '.data[] | {id, type, description}'
```

## Tool Naming Conventions

- **Workflow tools**: `tool-workflow-<workflow-name>`
- **ES|QL tools**: `tool-esql-<query-name>`
- **Index search tools**: `tool-search-<index-name>`

## Description Best Practices

- Be specific about what the tool does
- Mention key parameters or inputs
- Explain what data it returns
- Use action verbs: "Retrieve", "Search", "Get", "Calculate"

**Good examples:**
- "Retrieve customer profile including purchase history and loyalty tier"
- "Search the product catalog for gear recommendations"
- "Get top gear preference tags from user browsing behavior"

**Bad examples:**
- "Customer tool"
- "Search"
- "Gets stuff"

## Tool Configuration

### Workflow Tool

```json
{
  "configuration": {
    "workflow_id": "abc123-def456-ghi789"
  }
}
```

### ES|QL Tool

```json
{
  "configuration": {
    "query": "FROM index | WHERE field == 'value' | STATS count = COUNT(*)",
    "params": {}
  }
}
```

### Index Search Tool

```json
{
  "configuration": {
    "pattern": "index-name"
  }
}
```

## Verify Tool

```bash
curl -s -X GET "$KIBANA_URL/api/agent_builder/tools" \
  -H "Authorization: ApiKey $ES_APIKEY" \
  -H "kbn-xsrf: true" \
  -H "x-elastic-internal-origin: kibana" \
  | jq '.data[] | select(.id=="tool-workflow-example")'
```

## Delete Tool

```bash
curl -X DELETE "$KIBANA_URL/api/agent_builder/tools/tool-workflow-example" \
  -H "Authorization: ApiKey $ES_APIKEY" \
  -H "kbn-xsrf: true" \
  -H "x-elastic-internal-origin: kibana"
```

## Tips

- Tool descriptions are critical - agents use them to decide when to call tools
- Keep descriptions concise but informative
- Use consistent naming conventions
- Verify workflow exists before creating workflow tool
- Tools appear in Agent Builder UI after creation

