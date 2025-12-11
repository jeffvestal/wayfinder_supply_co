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
  path: /app/chat
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

## Step 1: Navigate to Agent Builder

1. Click the [button label="Kibana Agent Builder"](tab-0) tab

2. In the left sidebar, click **Tools**
   <!-- SCREENSHOT: Kibana left sidebar with "Tools" highlighted under AI Assistant section -->

3. You'll see a list of existing tools (some were pre-created for the workshop)
   <!-- SCREENSHOT: Tools list showing pre-existing tools like product_search -->

---

## Step 2: Create a New Tool

1. Click the **Create tool** button in the upper right
   <!-- SCREENSHOT: "Create tool" button location -->

2. You'll see the tool creation form with several options

---

## Step 3: Configure the Tool

Fill in the tool configuration:

**Basic Information:**

| Field | Value |
|-------|-------|
| **Tool ID** | `tool-workflow-get-customer-profile` |
| **Tool Type** | Select **Workflow** from the dropdown |
| **Description** | `Retrieve customer profile including purchase history and loyalty tier from CRM` |

<!-- SCREENSHOT: Tool creation form with basic fields filled in -->

---

## Step 4: Select the Workflow

1. In the **Workflow** dropdown, select `get_customer_profile`
   <!-- SCREENSHOT: Workflow dropdown showing get_customer_profile option -->

2. If you don't see it:
   - Go back to Challenge 2 and ensure the workflow was saved
   - Refresh the page and try again

---

## Step 5: Save the Tool

1. Click **Save tool** (or **Create** depending on UI version)
   <!-- SCREENSHOT: Save/Create button highlighted -->

2. You should see a success message

3. Your tool now appears in the tools list!
   <!-- SCREENSHOT: Tools list showing the newly created tool -->

---

## Step 6: Verify the Tool

1. Find your tool in the list: `tool-workflow-get-customer-profile`

2. Click on it to view its configuration

3. Verify:
   - **Type**: Workflow
   - **Workflow**: get_customer_profile
   - **Description**: Mentions customer profile and CRM
   <!-- SCREENSHOT: Tool detail view showing configuration -->

---

## Understanding Tool Descriptions

The tool description is **critical** for agent behavior!

Agents read descriptions to decide when to use a tool. A good description:
- Clearly states what data the tool returns
- Mentions keywords agents will recognize
- Is specific about the tool's purpose

**Good**: "Retrieve customer profile including purchase history and loyalty tier from CRM"

**Bad**: "Gets customer data" (too vague)

---

## Understanding Other Tools

While you built a workflow tool, the system also includes:

**Index Search Tool** (`product_search`):
- Type: Index Search
- Searches the `product-catalog` index
- Used by agents to find and recommend products

**ES|QL Tool** (`get_user_affinity`):
- Type: ES|QL
- Executes a query to analyze browsing behavior
- Returns top preference tags for personalization

You can click on these tools to see their configuration!

---

## How Agents Use Tools

When an agent needs customer information, it will:

1. **See your tool** in its available tools list
2. **Read the description**: "Retrieve customer profile..."
3. **Decide to call it** when the user asks about their account
4. **Pass parameters**: The `user_id` input
5. **Receive results**: Customer profile data from the workflow
6. **Use the data**: Personalize recommendations based on loyalty tier

This is the power of agentic search - the agent automatically knows when and how to get customer context!

---

## Verification Checklist

Your tool should:
- ✅ Be created and visible in Agent Builder Tools
- ✅ Have type "Workflow"
- ✅ Be linked to `get_customer_profile` workflow
- ✅ Have a clear, descriptive description

Once verified, click **Check** to proceed to the next challenge: **Building an Agent** that uses your tool!

---

## Troubleshooting

**Tool not appearing in list?**
- Refresh the page
- Check that you clicked Save/Create
- Verify there were no validation errors

**Workflow not in dropdown?**
- Return to Kibana Workflows and verify it's saved
- The workflow name should be `get_customer_profile`
- Wait a moment and refresh - there may be a sync delay

**Need to see existing tools?**
- Click on `tool-search-product-search` to see how an index search tool is configured
- Click on `tool-esql-get-user-affinity` to see an ES|QL tool example

---

## Next Steps

In the next challenge, you'll create an agent that uses this tool (along with others) to orchestrate trip planning. The agent will automatically call your tool when it needs customer information!
