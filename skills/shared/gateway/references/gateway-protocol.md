# Gateway Protocol (MCP JSON-RPC)

All calls: `{gateway_endpoint}/mcp`, JSON-RPC over HTTP.

- Tool name: `{target_prefix}___<operationId>` (prefix from env table in SKILL.md)
- Auth header: `Authorization: Bearer <access_token>`
- Envelope: `{data:{...}, context:{authServiceToken}, clientInterface:"DESKTOP", fields:[]}`
- `access_token` → `Authorization` header; `id_token` → `context.authServiceToken`

Response: `result.content[0].text` is the payload (JSON string or plain text). Parse it.

Never call `tools/list` — use `x_amz_bedrock_agentcore_search(name)` instead.
