# Agent Cheat Sheet

Quick reference for creating Agent Builder agents.

## Agent Structure

```json
{
  "id": "agent-id",
  "name": "Agent Name",
  "description": "What the agent does",
  "configuration": {
    "instructions": "System prompt defining agent behavior...",
    "tools": [{
      "tool_ids": ["tool-id-1", "tool-id-2"]
    }]
  }
}
```

## Create Agent via API

```bash
curl -X POST "$KIBANA_URL/api/agent_builder/agents" \
  -H "Authorization: ApiKey $ES_APIKEY" \
  -H "Content-Type: application/json" \
  -H "kbn-xsrf: true" \
  -H "x-elastic-internal-origin: kibana" \
  -d '{
    "id": "agent-id",
    "name": "Agent Name",
    "description": "Agent description",
    "configuration": {
      "instructions": "Instructions here...",
      "tools": [{
        "tool_ids": ["tool-id-1", "tool-id-2"]
      }]
    }
  }'
```

## Get Tool IDs

```bash
TOOLS_RESPONSE=$(curl -s -X GET "$KIBANA_URL/api/agent_builder/tools" \
  -H "Authorization: ApiKey $ES_APIKEY" \
  -H "kbn-xsrf: true" \
  -H "x-elastic-internal-origin: kibana")

TOOL_ID=$(echo "$TOOLS_RESPONSE" | jq -r '.data[] | select(.id=="tool-name") | .id')
```

## Instructions Best Practices

### Role Definition

```
You are the [Role Name]. Your role is to [primary function].
```

### Critical Rules

```
## CRITICAL RULE: [Rule Name]

**NEVER do [forbidden action]**

You MUST:
1. Always [required action]
2. Only [restriction]
3. Include [required element]
```

### Step-by-Step Process

```
## PROCESS STEPS

1. **Step 1**: Use [tool] to [action]
2. **Step 2**: Use [tool] to [action]
3. **Step 3**: [Action] based on results
```

### Output Format

```
Format your response as clean Markdown.

For each [item], use this format:
- **[Name]** - [Details] ([reason])

Example: **Item Name** - $123.45 (reason it fits)
```

## Example Instructions Template

```
You are the [Role]. Your role is to [primary function].

## CRITICAL RULE: [Rule Name]

**NEVER [forbidden action]**

You MUST:
1. ALWAYS use [tool] BEFORE [action]
2. ONLY [restriction]
3. Include [required element]

## PROCESS STEPS

1. **Step 1**: Use [tool] to [action]
2. **Step 2**: Use [tool] to [action]
3. **Step 3**: Synthesize results

Format your response as clean Markdown.
```

## List Agents

```bash
curl -s -X GET "$KIBANA_URL/api/agent_builder/agents" \
  -H "Authorization: ApiKey $ES_APIKEY" \
  -H "kbn-xsrf: true" \
  -H "x-elastic-internal-origin: kibana" \
  | jq '.data[] | {id, name, tool_count: (.configuration.tools[0].tool_ids | length)}'
```

## Get Agent Details

```bash
curl -s -X GET "$KIBANA_URL/api/agent_builder/agents" \
  -H "Authorization: ApiKey $ES_APIKEY" \
  -H "kbn-xsrf: true" \
  -H "x-elastic-internal-origin: kibana" \
  | jq '.data[] | select(.id=="agent-id")'
```

## Test Agent

1. Navigate to **Machine Learning** → **Agent Builder** → **Agents**
2. Click on your agent
3. Click **Test**
4. Enter a query
5. Watch tool calls in execution trace

## Tool Assignment

### Single Tool

```json
{
  "tools": [{
    "tool_ids": ["tool-id-1"]
  }]
}
```

### Multiple Tools

```json
{
  "tools": [{
    "tool_ids": ["tool-id-1", "tool-id-2", "tool-id-3"]
  }]
}
```

## Agent Description

Keep it concise and descriptive:

**Good:**
- "Main orchestrator agent that plans trips and recommends gear based on location, weather, customer profile, and preferences"
- "Synthesizes trip plans and creates formatted itineraries with gear checklists"

**Bad:**
- "Trip agent"
- "Does stuff"

## Tips

- Instructions should be clear and specific
- Mention tool names explicitly in instructions
- Define the decision-making process step-by-step
- Include output format guidelines
- Test agents thoroughly before production use
- Review execution logs to understand agent behavior
- Tool descriptions help agents decide when to call them

## Common Patterns

### Orchestrator Agent

- Uses multiple tools
- Chains tool calls together
- Synthesizes results
- Makes decisions based on tool outputs

### Parser Agent

- No tools needed
- Extracts structured data
- Returns JSON only
- Used by other agents

### Content Generator Agent

- May use tools for context
- Formats output
- Applies business rules
- Creates user-facing content

