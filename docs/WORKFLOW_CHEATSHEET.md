# Workflow Cheat Sheet

Quick reference for building Elastic Workflows.

## Basic Structure

```yaml
version: "1"
name: workflow_name
enabled: true

inputs:
  - name: input_name
    type: string
    required: true
    description: "Input description"

triggers:
  - type: manual

steps:
  - name: step_name
    type: step_type
    with:
      # Step configuration
```

## Input Types

- `string` - Text values
- `number` - Numeric values
- `boolean` - True/false values
- `array` - Lists of values
- `object` - Complex nested structures

## Step Types

### HTTP Step

```yaml
- name: call_api
  type: http
  with:
    url: "http://host-1:8002/api"
    method: POST
    headers:
      Content-Type: application/json
    body:
      key: "{{ inputs.value }}"
  on-failure:
    retry:
      max-attempts: 2
      delay: 1s
```

### Console Step

```yaml
- name: log_message
  type: console
  with:
    message: |
      Customer: {{ inputs.user_id }}
      Result: {{ steps.call_api.output.data.result }}
```

### ES|QL Query Step

```yaml
- name: query_data
  type: elasticsearch.esql.query
  with:
    query: >
      FROM user-clickstream
      | WHERE user_id == "{{ inputs.user_id }}"
      | STATS count = COUNT(*) BY tag
      | SORT count DESC
```

### Elasticsearch Search Step

```yaml
- name: search_index
  type: elasticsearch.search
  with:
    index: "product-catalog"
    query:
      match:
        name: "{{ inputs.search_term }}"
    size: 10
```

## Liquid Templating

### Variables

```yaml
{{ inputs.user_id }}                    # Input variable
{{ steps.step_name.output }}            # Step output
{{ execution.id }}                      # Execution ID
{{ execution.startedAt }}                # Execution timestamp
```

### Filters

```yaml
{{ value | size }}                      # Array/object size
{{ value | default: 'N/A' }}           # Default value
{{ date | date: '%Y-%m-%d' }}          # Date formatting
{{ value | json_parse }}                # Parse JSON string
```

### Conditionals

```yaml
{% if steps.check.output == "success" %}
  ✅ Success
{% else %}
  ❌ Failed
{% endif %}
```

### Accessing Nested Data

```yaml
{{ steps.call_api.output.data.result.name }}
{{ steps.query.output.values[0][0] }}
{{ steps.search.output.hits.hits[0]._source.title }}
```

## Common Patterns

### MCP Server Call

```yaml
- name: call_mcp
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
        name: "tool_name"
        arguments:
          param: "{{ inputs.value }}"
      id: "{{ execution.id }}"
```

### Error Handling

```yaml
on-failure:
  retry:
    max-attempts: 2
    delay: 1s
```

### Conditional Steps

```yaml
- name: check_condition
  type: if
  condition: "${{ steps.get_value.output > 100 }}"
  steps:
    - name: take_action
      type: console
      with:
        message: "Value exceeded threshold"
```

## API Headers

Required headers for Kibana API calls:

```bash
-H "Authorization: ApiKey $ES_APIKEY"
-H "Content-Type: application/json"
-H "kbn-xsrf: true"
-H "x-elastic-internal-origin: kibana"  # REQUIRED for workflows API
```

## Deploy Workflow

```bash
curl -X POST "$KIBANA_URL/api/workflows" \
  -H "Authorization: ApiKey $ES_APIKEY" \
  -H "Content-Type: application/json" \
  -H "kbn-xsrf: true" \
  -H "x-elastic-internal-origin: kibana" \
  -d '{"yaml": "<yaml_content>"}'
```

## Execute Workflow

```bash
curl -X POST "$KIBANA_URL/api/workflows/$WORKFLOW_ID/_execute" \
  -H "Authorization: ApiKey $ES_APIKEY" \
  -H "Content-Type: application/json" \
  -H "kbn-xsrf: true" \
  -H "x-elastic-internal-origin: kibana" \
  -d '{"input": {"key": "value"}}'
```

## Tips

- Always use `x-elastic-internal-origin: kibana` header for workflows API
- Use retry logic for external API calls
- Access step outputs with `steps.step_name.output`
- Use Liquid filters for data transformation
- Test workflows via API before using in agents

