# Gateway Protocol (MCP JSON-RPC)

All calls: `{gateway_endpoint}/mcp`, JSON-RPC over HTTP.

- Tool name: `{target_prefix}___<operationId>` (prefix from env table in SKILL.md)
- Auth header: `Authorization: Bearer <access_token>`
- Envelope: `{data:{...}, context:{authServiceToken}, clientInterface:"DESKTOP", fields:[]}`
- `access_token` → `Authorization` header; `id_token` → `context.authServiceToken`

Response: `result.content[0].text` is the payload (JSON string or plain text). Parse it.

Never call `tools/list` — use `x_amz_bedrock_agentcore_search(name)` instead.

## Schema Search

Search uses bare arguments, not the tool-call envelope:

```bash
curl -s -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","id":"1","params":{"name":"x_amz_bedrock_agentcore_search","arguments":{"query":"<operation_name>"}}}' \
  {gateway_endpoint}/mcp
```

## Tool Call

Build `data` from the schema returned by search. Normalize values using the domain skill, then call the prefixed tool:

```bash
curl -s -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","id":"1","params":{"name":"{prefix}___<operation_name>","arguments":{"data":{...},"context":{"authServiceToken":"<id_token>"},"clientInterface":"DESKTOP","fields":[]}}}' \
  {gateway_endpoint}/mcp
```
