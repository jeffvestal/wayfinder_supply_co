---
slug: build-workflow
id: izndj9o584gm
type: challenge
title: Build a Workflow
teaser: Create a workflow that connects to external systems and retrieves customer
  data
tabs:
- id: mzsvd6hetpqv
  title: Kibana Workflows
  type: service
  hostname: kubernetes-vm
  path: /app/workflows
  port: 30001
- id: zzux5pxawd9r
  title: Code Editor
  type: code
  hostname: host-1
  path: /opt/workshop-assets
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

## Step 1: Open Kibana Workflows UI

1. Click the [button label="Kibana Workflows"](tab-0) tab

2. You should see the Workflows management page
   <!-- SCREENSHOT: Kibana Workflows landing page showing the workflow list -->

3. Click **Create workflow** button in the upper right
   <!-- SCREENSHOT: Arrow pointing to "Create workflow" button -->

---

## Step 2: Configure the Workflow

In the workflow editor:

1. **Name**: Enter `get_customer_profile`

2. **Description**: Enter "Retrieves customer profile data from CRM including loyalty tier and purchase history"

3. Switch to **YAML editor** view (toggle in the top right of the editor)
   <!-- SCREENSHOT: Toggle showing YAML editor option -->

---

## Step 3: Enter the Workflow YAML

Paste the following YAML into the editor:

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

## Understanding the YAML

Let's break down the key sections:

**Inputs:**
```yaml
inputs:
  - name: user_id
    type: string
    required: true
```
- Defines parameters the workflow accepts
- `user_id` is required to look up the customer

**HTTP Step:**
```yaml
steps:
  - name: call_crm_mcp
    type: http
    with:
      url: "http://host-1:8002/mcp"
```
- Calls the MCP (Mock CRM/Weather) server
- Uses JSON-RPC protocol to invoke tools
- `{{ inputs.user_id }}` - Liquid template to inject the input value

**Console Output:**
```yaml
  - name: log_profile
    type: console
    with:
      message: |
        Customer Profile for {{ inputs.user_id }}:
```
- Logs results for debugging
- `steps.call_crm_mcp.output` - Access previous step's output
- `| size` - Liquid filter to get array length

---

## Step 4: Save the Workflow

1. Click **Save workflow** button
   <!-- SCREENSHOT: Save workflow button highlighted -->

2. You should see a success message
   <!-- SCREENSHOT: Success toast notification -->

3. Your workflow now appears in the workflow list
   <!-- SCREENSHOT: Workflow list showing get_customer_profile -->

---

## Step 5: Test the Workflow

1. Click on your `get_customer_profile` workflow to open it

2. Click the **Run** button (or **Execute** depending on UI version)
   <!-- SCREENSHOT: Run/Execute button location -->

3. In the input dialog, enter a test user ID:
   ```
   user_member
   ```
   <!-- SCREENSHOT: Input dialog with user_member entered -->

4. Click **Run**

5. View the execution results:
   - You should see the workflow complete successfully ✅
   - The console output shows customer data
   - Review the returned profile information
   <!-- SCREENSHOT: Successful execution with console output visible -->

---

## Verify Your Results

Your workflow execution should show:

```
Customer Profile for user_member:
Name: Alex Thompson
Loyalty Tier: platinum
Lifetime Value: $8450.00
Purchase History: 12 items
```

If you see different output, that's OK - it just means you're using a different test user!

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

## Verification Checklist

Your workflow should:
- ✅ Be created and visible in Kibana Workflows
- ✅ Accept `user_id` as input
- ✅ Successfully call the MCP server
- ✅ Return customer profile data when executed

Once verified, click **Check** to proceed to the next challenge: **Building a Tool** that wraps this workflow!

---

## Troubleshooting

**Workflow validation errors?**
- Check YAML syntax (indentation matters!)
- Ensure all required fields are present
- Use the YAML validator in the editor

**Execution failing?**
- Verify the MCP server is running on port 8002
- Check the URL in the HTTP step
- Review error messages in the execution logs

**Need to see the raw YAML again?**
- Reference file at `config/workflows/get_customer_profile.yaml` in [button label="Code Editor"](tab-1)
