---
slug: build-tool
id: zspkqmjda68g
type: challenge
title: Build a Tool
teaser: Wrap your workflow as a tool that agents can use
tabs:
- id: ru07u4jacjov
  title: Kibana Agent Builder
  type: service
  hostname: kubernetes-vm
  path: /app/agent_builder
  port: 30001
- id: jxurvygvav1x
  title: Terminal
  type: terminal
  hostname: host-1
difficulty: intermediate
timelimit: 1200
enhanced_loading: null
---

# Build a Tool

Now that you've created a workflow, you need to make it available to agents. In this challenge, you'll create a **tool** that wraps your `get_customer_profile` workflow.

---

## What You'll Build

You'll create a workflow tool that:
- Wraps the `get_customer_profile` workflow you built in Challenge 2
- Makes it available to agents in Agent Builder
- Allows agents to retrieve customer profiles automatically

---

## Understanding Tools

**Tools** are the interface between agents and external capabilities. There are three types:

1. **Workflow Tools** - Wrap Elastic Workflows
2. **ES|QL Tools** - Execute ES|QL queries directly
3. **Index Search Tools** - Search Elasticsearch indices

When an agent needs to retrieve customer data, it calls your workflow tool, which executes the workflow and returns the results.

---

## Step 1: Get Your Workflow ID

First, you need the ID of the workflow you created in Challenge 2:

1. Open the [button label="Terminal"](tab-1) tab

2. Get the workflow ID:

```bash
export KIBANA_URL="http://kubernetes-vm:30001"
export ES_APIKEY="${STANDALONE_ELASTICSEARCH_APIKEY}"

WORKFLOW_ID=$(curl -s -X GET "$KIBANA_URL/api/workflows" \
  -H "Authorization: ApiKey $ES_APIKEY" \
  -H "kbn-xsrf: true" \
  -H "x-elastic-internal-origin: kibana" \
  | jq -r '.data[] | select(.name=="get_customer_profile") | .id')

echo "Workflow ID: $WORKFLOW_ID"
```

Save this ID - you'll need it in the next step!

---

## Step 2: Create the Tool

Create a workflow tool using the Agent Builder API:

```bash
curl -X POST "$KIBANA_URL/api/agent_builder/tools" \
  -H "Authorization: ApiKey $ES_APIKEY" \
  -H "Content-Type: application/json" \
  -H "kbn-xsrf: true" \
  -H "x-elastic-internal-origin: kibana" \
  -d "{
    \"id\": \"tool-workflow-get-customer-profile\",
    \"type\": \"workflow\",
    \"description\": \"Retrieve customer profile including purchase history and loyalty tier from CRM\",
    \"configuration\": {
      \"workflow_id\": \"$WORKFLOW_ID\"
    }
  }"
```

**Key Fields:**
- `id`: Unique identifier for the tool (use `tool-workflow-` prefix)
- `type`: Must be `"workflow"` for workflow tools
- `description`: What the tool does (agents use this to decide when to call it)
- `configuration.workflow_id`: The ID of your workflow from Step 1

---

## Step 3: Verify the Tool

Check that your tool was created successfully:

```bash
curl -s -X GET "$KIBANA_URL/api/agent_builder/tools" \
  -H "Authorization: ApiKey $ES_APIKEY" \
  -H "kbn-xsrf: true" \
  -H "x-elastic-internal-origin: kibana" \
  | jq '.data[] | select(.id=="tool-workflow-get-customer-profile")'
```

You should see your tool in the response!

---

## Step 4: View in Agent Builder UI

1. Open the [button label="Kibana Agent Builder"](tab-0) tab

2. Navigate to **Machine Learning** → **Agent Builder** → **Tools**

3. You should see your tool listed:
   - **ID**: `tool-workflow-get-customer-profile`
   - **Type**: Workflow
   - **Description**: Retrieve customer profile...

4. Click on your tool to see its configuration

---

## Understanding Other Tools

While you built a workflow tool, the system also includes:

**Index Search Tool** (`product_search`):
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
- Searches the `product-catalog` index
- Used by agents to find products

**ES|QL Tool** (`get_user_affinity`):
```json
{
  "id": "tool-esql-get-user-affinity",
  "type": "esql",
  "description": "Get top gear preference tags from user browsing behavior",
  "configuration": {
    "query": "FROM user-clickstream | WHERE meta_tags IS NOT NULL | STATS count = COUNT(*) BY meta_tags | SORT count DESC | LIMIT 5"
  }
}
```
- Executes ES|QL queries directly
- Used for analytics and aggregations

---

## How Agents Use Tools

When an agent needs customer information, it will:
1. See your tool in its available tools list
2. Read the description: "Retrieve customer profile..."
3. Decide to call it when the user asks about their account or preferences
4. Pass the `user_id` parameter
5. Receive the customer profile data
6. Use that data to personalize recommendations

---

## Verification

Your tool should:
- ✅ Be created and visible in Agent Builder
- ✅ Have the correct workflow_id configured
- ✅ Have a clear description
- ✅ Appear in the tools list

Once verified, you're ready for the next challenge: **Building an Agent** that uses your tool!

---

## Troubleshooting

**Tool not appearing?**
- Verify the workflow exists: `curl -s "$KIBANA_URL/api/workflows" ... | jq '.data[] | .name'`
- Check that you used the correct workflow_id
- Ensure you included the `x-elastic-internal-origin: kibana` header

**API errors?**
- Check that your API key has the correct permissions
- Verify Kibana URL is correct: `echo $KIBANA_URL`

**Need help?**
- Review tool examples in Agent Builder UI
- Check `docs/TOOL_CHEATSHEET.md` in the repo for reference (TODO: add as tab)

---

## Next Steps

In the next challenge, you'll create an agent that uses this tool (along with others) to orchestrate trip planning. The agent will automatically call your tool when it needs customer information!

