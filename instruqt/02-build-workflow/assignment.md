---
slug: build-workflow
id: izndj9o584gm
type: challenge
title: Build a Workflow
teaser: Create a workflow that connects to external systems and retrieves customer
  data
tabs:
- id: zzux5pxawd9r
  title: Code Editor
  type: code
  hostname: host-1
  path: /opt/workshop-assets
- id: mzsvd6hetpqv
  title: Kibana Workflows
  type: service
  hostname: kubernetes-vm
  path: /app/workflows
  port: 30001
- id: cgn8ifagnwx1
  title: Terminal
  type: terminal
  hostname: host-1
difficulty: intermediate
timelimit: 1500
enhanced_loading: null
---

# Build a Workflow

In this challenge, you'll create a workflow that connects to the MCP server to retrieve customer profile data. This workflow will be used by agents to understand customer preferences and purchase history.

---

## What You'll Build

You'll create the `get_customer_profile` workflow that:
1. Accepts a `user_id` as input
2. Calls the MCP server's CRM service
3. Returns customer profile data including loyalty tier and purchase history

---

## Understanding Workflows

**Elastic Workflows** are YAML-based automation that can:
- Call external APIs (like our MCP server)
- Query Elasticsearch using ES|QL
- Chain multiple steps together
- Be used as tools by agents

**Key Concepts:**
- **Inputs**: Parameters the workflow accepts
- **Steps**: Individual actions (HTTP calls, ES|QL queries, console output)
- **Liquid Templating**: Dynamic values using `{{ }}` syntax

---

## Step 1: Create the Workflow File

1. Open the [button label="Code Editor"](tab-0) tab

2. Create a new file: `config/workflows/get_customer_profile.yaml`

3. Start with the basic structure:

```yaml
version: "1"
name: get_customer_profile
enabled: true

inputs:
  - name: user_id
    type: string
    required: true
    description: "The user identifier (e.g., 'user_new', 'user_member', 'user_business')"

triggers:
  - type: manual

steps:
  # Your steps will go here
```

---

## Step 2: Add the HTTP Step

Add a step that calls the MCP server. The MCP server uses JSON-RPC protocol:

```yaml
steps:
  - name: call_crm_mcp
    type: http
    with:
      url: "http://host-1:8002/mcp"
      method: POST
      headers:
        Content-Type: application/json
      body:
        jsonrpc: "2.0"
        method: "tools/call"
        params:
          name: "get_customer_profile_tool"
          arguments:
            user_id: "{{ inputs.user_id }}"
        id: "{{ execution.id }}"
    on-failure:
      retry:
        max-attempts: 2
        delay: 1s
```

**Key Points:**
- `{{ inputs.user_id }}` - Liquid template to inject the input value
- `{{ execution.id }}` - Unique execution ID for this workflow run
- `on-failure` - Retry logic for resilience

---

## Step 3: Add Console Output Step

Add a step to log the customer profile:

```yaml
  - name: log_profile
    type: console
    with:
      message: |
        Customer Profile for {{ inputs.user_id }}:
        Name: {{ steps.call_crm_mcp.output.data.result.name }}
        Loyalty Tier: {{ steps.call_crm_mcp.output.data.result.loyalty_tier }}
        Lifetime Value: ${{ steps.call_crm_mcp.output.data.result.lifetime_value }}
        Purchase History: {{ steps.call_crm_mcp.output.data.result.purchase_history | size }} items
```

**Key Points:**
- `steps.call_crm_mcp.output` - Access the previous step's output
- `| size` - Liquid filter to get array size
- Multi-line message using `|` YAML syntax

---

## Step 4: Complete Workflow

Your complete workflow should look like this:

```yaml
version: "1"
name: get_customer_profile
enabled: true

inputs:
  - name: user_id
    type: string
    required: true
    description: "The user identifier (e.g., 'user_new', 'user_member', 'user_business')"

triggers:
  - type: manual

steps:
  - name: call_crm_mcp
    type: http
    with:
      url: "http://host-1:8002/mcp"
      method: POST
      headers:
        Content-Type: application/json
      body:
        jsonrpc: "2.0"
        method: "tools/call"
        params:
          name: "get_customer_profile_tool"
          arguments:
            user_id: "{{ inputs.user_id }}"
        id: "{{ execution.id }}"
    on-failure:
      retry:
        max-attempts: 2
        delay: 1s

  - name: log_profile
    type: console
    with:
      message: |
        Customer Profile for {{ inputs.user_id }}:
        Name: {{ steps.call_crm_mcp.output.data.result.name }}
        Loyalty Tier: {{ steps.call_crm_mcp.output.data.result.loyalty_tier }}
        Lifetime Value: ${{ steps.call_crm_mcp.output.data.result.lifetime_value }}
        Purchase History: {{ steps.call_crm_mcp.output.data.result.purchase_history | size }} items
```

---

## Step 5: Deploy the Workflow via Kibana UI

1. Open the [button label="Kibana Workflows"](tab-1) tab

2. Navigate to the Workflows UI:
   - Click the **hamburger menu** (☰) in the top-left corner
   - Go to **Management** → **Workflows**
   - You should see the Workflows UI with a list of existing workflows

3. Create a new workflow:
   - Click **"Create a new workflow"** button
   - This opens the YAML editor

4. Copy your complete workflow YAML from Step 4 and paste it into the editor

5. Click **"Save"** to deploy the workflow

The workflow will be automatically saved and enabled. You should see it appear in the workflows list!

**Note:** The Workflows UI is a YAML editor - you're editing the same YAML format you created in the Code Editor. This is the recommended way to create and manage workflows.

---

## Step 6: Test the Workflow

Test your workflow using the Kibana UI:

1. In the [button label="Kibana Workflows"](tab-1) tab, find your `get_customer_profile` workflow in the list

2. Click on the workflow name to open it

3. Click the **"Run workflow"** or **"Execute"** button

4. In the input dialog, enter:
   ```json
   {
     "user_id": "user_member"
   }
   ```

5. Click **"Run"** to execute the workflow

6. View the execution results:
   - The console output step will show the customer profile information
   - Check the execution logs to see the full response from the MCP server

You should see output like:
```
Customer Profile for user_member:
Name: Sarah Martinez
Loyalty Tier: Platinum
Lifetime Value: $2847.50
Purchase History: 12 items
```

---

## Understanding Other Workflows

While you built `get_customer_profile`, the system also includes:

**check_trip_safety** - Similar HTTP pattern but calls weather service:
- Calls `get_trip_conditions_tool` on MCP server
- Returns weather conditions and road alerts
- Used by agents to assess trip safety

**get_user_affinity** - ES|QL query pattern:
- Queries `user-clickstream` index
- Analyzes browsing behavior
- Returns top preference tags

You can explore these in Kibana to see different workflow patterns!

---

## Verification

Your workflow should:
- ✅ Be deployed and visible in Kibana
- ✅ Accept `user_id` as input
- ✅ Successfully call the MCP server
- ✅ Return customer profile data

Once verified, you're ready for the next challenge: **Building a Tool** that wraps this workflow!

---

## Troubleshooting

**Workflow not appearing?**
- Check that you included the `x-elastic-internal-origin: kibana` header
- Verify the YAML syntax is correct (use a YAML validator)

**MCP call failing?**
- Ensure the MCP server is running: `docker ps | grep mcp`
- Check MCP server logs: `docker logs wayfinder-mcp-server`

**Need help?**
- Review the workflow execution logs in Kibana
- Check `docs/WORKFLOW_CHEATSHEET.md` in the repo for reference (TODO: add as tab)

