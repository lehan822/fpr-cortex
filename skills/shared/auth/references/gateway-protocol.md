# Gateway Protocol (MCP JSON-RPC)

## Endpoint

All requests go to `{gateway_endpoint}/mcp` using POST with JSON body.

## Tool Discovery (tools/list)

Gateway paginates tools at **30 per page**. Always handle `nextCursor`:

```bash
# Page 1
curl -s -X POST "{gateway_endpoint}/mcp" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# If response has nextCursor, fetch next page:
curl -s -X POST "{gateway_endpoint}/mcp" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{"cursor":"<nextCursor>"}}'
```

Total tools: **55** across 2 pages. Always paginate until `nextCursor` is absent.

## Tool Naming Convention

⚠️ Gateway prefixes tool names with target name: `fprtool-backend___<operationId>`

- ✅ `fprtool-backend___load_commission_incentive_rules`
- ❌ `load_commission_incentive_rules` (will fail with "tool not found")

## Request Format (tools/call)

⚠️ **Traveloka Request Envelope:** All tool parameters MUST be wrapped inside `data`.

| Field | Required | Description |
|-------|----------|-------------|
| `data` | ✅ | Contains all tool-specific parameters |
| `context` | ✅ | Must include `authServiceToken` (id_token) |
| `clientInterface` | ✅ | Always `"DESKTOP"` |
| `fields` | ✅ | Always `[]` |

```bash
curl -s -X POST "{gateway_endpoint}/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer {access_token_from_auth_json}" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "id": "1",
    "params": {
      "name": "fprtool-backend___<operationId>",
      "arguments": {
        "data": {
          "<param1>": "<value1>",
          "<param2>": "<value2>"
        },
        "context": {
          "authServiceToken": "<id_token_from_auth_json>"
        },
        "clientInterface": "DESKTOP",
        "fields": []
      }
    }
  }'
```

## Example — Query GA Commission Rules (staging)

```bash
curl -s -X POST "https://fpr-lehan-jwt-gw-z6tsij9aib.gateway.bedrock-agentcore.ap-southeast-1.amazonaws.com/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $(cat ~/.fpr/auth.json | node -e \"process.stdin.on('data',d=>console.log(JSON.parse(d).access_token))\")" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "id": "1",
    "params": {
      "name": "fprtool-backend___load_commission_incentive_rules",
      "arguments": {
        "data": {
          "airline": "GA"
        },
        "context": {
          "authServiceToken": "'$(cat ~/.fpr/auth.json | node -e "process.stdin.on('data',d=>console.log(JSON.parse(d).id_token))")'"
        },
        "clientInterface": "DESKTOP",
        "fields": []
      }
    }
  }'
```

## Response Format

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": {
    "content": [{ "type": "text", "text": "..." }]
  }
}
```

## Key Points

- `Authorization` header → `access_token` (Cognito, for Gateway auth)
- `arguments.context.authServiceToken` → `id_token` (for fprtool-backend user identity)
- `arguments.data` → all tool-specific params go inside `data` wrapper
- `name` = `fprtool-backend___<operationId>` (with target prefix)
- All operations use `method: "tools/call"`
