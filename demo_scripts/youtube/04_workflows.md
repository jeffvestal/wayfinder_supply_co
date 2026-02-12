# YouTube Video: Workflows - Building the Agent's Hands

**Target Duration:** 8-10 minutes
**Audience:** Developers on Elastic Community YouTube channel
**Focus:** Creating workflow tools that call external APIs via MCP

---

## Section A: Verbal Script

### Intro (0:00-1:00)

"In the last videos, you saw our Trip Planner agent check weather conditions and look up customer profiles. But where did that data come from?

The agent didn't magically know the weather in Yosemite. It called a workflow - and that workflow made an external API call to fetch real data.

Today I'm going to show you how to build workflows in Elastic. Think of Agent Builder as the brain - it decides what to do. Workflows are the hands - they actually do it.

By the end of this video, you'll know how to:
1. Create a workflow in YAML
2. Connect it to external APIs using MCP
3. Give it to an agent as a tool

Let's build."

### Key Points (1:00-8:00)

**Point 1: What Are Workflows? (1:00-2:00)**

"Workflows are YAML definitions that describe a sequence of steps. Each step can:
- Call external HTTP APIs
- Execute Elasticsearch queries
- Transform data with Liquid templating
- Chain results to the next step

When you register a workflow as a tool in Agent Builder, the agent can call it when it needs that data. The workflow executes, returns a result, and the agent incorporates it into its response.

The key difference from agent tools alone: workflows can make external HTTP calls. Agents can't directly call your CRM or weather API - but a workflow can."

**Point 2: Anatomy of a Workflow (2:00-3:30)**

"Let me show you a workflow that checks trip conditions. Here's the YAML:

```yaml
version: '1'
name: check_trip_safety
enabled: true

inputs:
  - name: location
    type: string
    required: true
  - name: dates
    type: string
    required: true

steps:
  - name: call_weather_mcp
    type: http
    with:
      url: 'http://mcp-server:8002/mcp'
      method: POST
      body:
        jsonrpc: '2.0'
        method: 'tools/call'
        params:
          name: 'get_trip_conditions_tool'
          arguments:
            location: '{{ inputs.location }}'
            dates: '{{ inputs.dates }}'
```

Let me break this down:

- `inputs` define what the workflow accepts. The agent passes location and dates.
- `steps` define what happens. This step makes an HTTP POST to our MCP server.
- `{{ inputs.location }}` is Liquid templating - it substitutes the actual values.

When this runs, it calls the weather service and returns conditions like temperature range, weather forecast, and road alerts."

**Point 3: Creating the Workflow in Kibana (3:30-5:00)**

"Let me show you how to create this in Kibana.

Navigate to Management → Workflows. Click Create Workflow.

You see a YAML editor. I'll paste in our check_trip_safety workflow.

The key fields:
- `name` must be unique - this becomes the workflow ID
- `enabled: true` makes it runnable
- `inputs` define the interface for callers
- `steps` define the execution

Save the workflow. Now it's deployed and ready to use.

Let me test it manually. Click Run, fill in the inputs: location 'Yosemite', dates 'March 15-18'.

Watch the execution. It calls the MCP server... and here are the results:
- Weather: partly cloudy
- Temperature: 28-52°F
- Road alert: chains may be required

The workflow successfully fetched external data."

**Point 4: The MCP Connection (5:00-6:30)**

"You might be wondering: what's this MCP server?

MCP - Model Context Protocol - is an open standard for giving AI agents access to tools. Our MCP server exposes weather and CRM services as MCP tools.

The workflow makes a JSON-RPC call to the MCP endpoint:

```json
{
  \"jsonrpc\": \"2.0\",
  \"method\": \"tools/call\",
  \"params\": {
    \"name\": \"get_trip_conditions_tool\",
    \"arguments\": {
      \"location\": \"Yosemite\",
      \"dates\": \"March 15-18\"
    }
  }
}
```

The MCP server receives this, calls the actual weather API (or a mock in our demo), and returns structured data.

This pattern - Workflow → MCP → External Service - is how you integrate any external system: Salesforce, Jira, ServiceNow, your internal APIs. The workflow handles the HTTP call, the MCP server handles the business logic."

**Point 5: Registering as an Agent Tool (6:30-7:30)**

"The final step: give this workflow to the agent.

Navigate to Agent Builder → Tools. Create a new tool:

- Tool ID: `tool-workflow-check-trip-safety`
- Type: `workflow`
- Description: 'Check weather and road conditions for a trip location and dates'
- Workflow ID: `check_trip_safety`

The description is critical - it tells the agent when to use this tool. A good description means the agent calls it at the right time.

Now go to the agent. Add this tool to the agent's tool list.

When someone asks 'What's the weather in Yosemite in March?' - the agent reads the tool description, decides it's relevant, and calls the workflow."

**Point 6: Another Example - Customer Profile (7:30-8:00)**

"We have another workflow: get_customer_profile. Same pattern:

```yaml
steps:
  - name: call_crm_mcp
    type: http
    with:
      url: 'http://mcp-server:8002/mcp'
      method: POST
      body:
        jsonrpc: '2.0'
        method: 'tools/call'
        params:
          name: 'get_customer_profile_tool'
          arguments:
            user_id: '{{ inputs.user_id }}'
```

This fetches CRM data: loyalty tier, lifetime value, purchase history. The agent uses this to check if you already own certain gear.

Same pattern, different data source. That's the power of workflows - standardized integration."

### Wrap-Up (8:00-8:30)

"That's workflows:
- YAML definitions for external data access
- HTTP steps to call APIs or MCP servers
- Registered as agent tools for AI orchestration

Agent Builder is the brain. Workflows are the hands. Together, they build agentic search applications.

In the final video, I'll walk through the complete end-to-end flow - from browsing the store to planning a trip to seeing the full architecture.

See you there."

---

## Section C: Full Demo Flow with Timestamps

**0:00-0:15** - Title card
- "Workflows: Building the Agent's Hands"

**0:15-1:00** - Hook
- "You saw the agent check weather. But how?"
- Show the thought trace from Video 01 with the workflow call
- "This is what we're building today"

**1:00-2:00** - Explain workflows conceptually
- Diagram: Agent → Workflow → MCP → External API
- "Agent Builder is the brain, workflows are the hands"

**2:00-2:30** - Navigate to Kibana Workflows
- Open Kibana
- Click hamburger menu → Management → Workflows
- "This is where workflows live"
- Show existing workflows list

**2:30-3:30** - Show check_trip_safety workflow
- Click on check_trip_safety
- Show the YAML
- Walk through each section:
  - "Inputs: location and dates"
  - "Steps: HTTP call to MCP server"
  - "Liquid templating: {{ inputs.location }}"

**3:30-4:30** - Create a new workflow (or show creation flow)
- Click "Create Workflow" (or show duplicate of existing)
- Paste/show the YAML structure
- "Name becomes the ID"
- "Inputs define the interface"
- "Steps define the execution"
- Save

**4:30-5:30** - Test the workflow manually
- Click "Run" on check_trip_safety
- Fill in inputs:
  - location: "Yosemite"
  - dates: "March 15-18"
- Click Execute
- Watch execution status
- Show results: weather, temp range, road alerts
- "The workflow called the external API and returned data"

**5:30-6:30** - Explain MCP connection
- Show the JSON-RPC body in the workflow
- Optionally show MCP server code briefly
- "MCP is the standard protocol"
- "Your MCP server can wrap any external API"

**6:30-7:30** - Show tool registration
- Navigate to Agent Builder → Tools
- Find tool-workflow-check-trip-safety
- Show the tool configuration:
  - Type: workflow
  - Description: what it does
  - Workflow ID: check_trip_safety
- "The description tells the agent when to use it"

**7:30-8:00** - Show get_customer_profile workflow
- Click on get_customer_profile
- "Same pattern - HTTP to MCP"
- "Fetches CRM data: loyalty tier, purchase history"
- "Reusable integration pattern"

**8:00-8:30** - Wrap up
- Show architecture diagram: Agent → Tools → Workflows → MCP → External
- "Brain + hands = agentic applications"
- "Next: Full end-to-end walkthrough"
- End screen

---

## B-Roll / Screenshot Suggestions

1. **Kibana Workflows list** - Show the management interface
2. **Workflow YAML editor** - Full check_trip_safety code
3. **Workflow execution** - Run dialog with inputs
4. **Workflow results** - Successful execution with weather data
5. **MCP JSON-RPC structure** - Code block showing the request format
6. **Tool registration** - Agent Builder tools interface
7. **Architecture diagram** - Agent → Workflow → MCP → External API

---

## Code Blocks for Reference

**check_trip_safety.yaml:**
```yaml
version: "1"
name: check_trip_safety
enabled: true

inputs:
  - name: location
    type: string
    required: true
    description: "The destination location"
  - name: dates
    type: string
    required: true
    description: "Date range for the trip"

steps:
  - name: call_weather_mcp
    type: http
    with:
      url: "http://mcp-server:8002/mcp"
      method: POST
      headers:
        Content-Type: application/json
      body:
        jsonrpc: "2.0"
        method: "tools/call"
        params:
          name: "get_trip_conditions_tool"
          arguments:
            location: "{{ inputs.location }}"
            dates: "{{ inputs.dates }}"
        id: "{{ execution.id }}"
    on-failure:
      retry:
        max-attempts: 2
        delay: 1s
```

**Tool Registration:**
```json
{
  "id": "tool-workflow-check-trip-safety",
  "type": "workflow",
  "description": "Check weather and road conditions for a trip destination. Returns temperature range, weather forecast, and road alerts. Call this when users mention a location they're traveling to.",
  "workflow_id": "check_trip_safety"
}
```
