---
name: fpr-shared
version: 2.9.0
description: "Flight Pricing & Revenue shared layer: auth, calling conventions, common parameter standards. Covers both local agents and AgentCore agents."
category: shared
---

# fpr-shared

> All FPR tools share the same auth, tool-name prefix, and envelope. This file covers what's common. Domain skills cover tool-specific knowledge.

## Auth

Call MCP tools directly. On 401, the agent handles it: run auth (may open browser) → start daemon → retry. Daemon keeps token fresh — no more 401s.

**AgentCore:** skip this — IAM handles it. Bootstrap → [`auth.md`](references/auth.md).

## Call Flow — schema-first

**All calls are HTTP POST to `{gateway_endpoint}/mcp` using JSON-RPC.** Use bash/curl — do NOT register as MCP server.

```
0. SELECT  → domain skill routes user intent to operation_name
1. SEARCH  → x_amz_bedrock_agentcore_search(operation_name) → get inputSchema
2. BUILD   → inputSchema.properties → data keys, normalized
3. CALL    → {prefix}___{operation_name} with data in envelope
```

Step 1 — SEARCH (bare args, **no envelope**):

```
curl -s -H "Authorization: Bearer <access_token>" \
  -d '{"jsonrpc":"2.0","method":"tools/call","id":"1","params":{"name":"x_amz_bedrock_agentcore_search","arguments":{"query":"<from step 0>"}}}' \
  {gateway_endpoint}/mcp
```

Step 2 — BUILD: each `inputSchema.properties` key → a key in `data`. Normalize values per domain skill rules. Cache schema.

Step 3 — CALL (with envelope):

```
curl -s -H "Authorization: Bearer <access_token>" \
  -d '{"jsonrpc":"2.0","method":"tools/call","id":"1","params":{"name":"{prefix}___<from step 0>","arguments":{"data":{<from step 2>},"context":{"authServiceToken":"<id_token>"},"clientInterface":"DESKTOP","fields":[]}}}' \
  {gateway_endpoint}/mcp
```

Full protocol → [`gateway-protocol.md`](references/gateway-protocol.md).

## Role split

| Component | Responsibility |
|-----------|----------------|
| **Domain skill** | User intent → operation_name + business gotchas |
| **Semantic search** | Authoritative inputSchema |
| **This file** | Auth, envelope, prefix, error handling |

## Environment (default: prod)

| Env | Prefix | Gateway |
|-----|--------|---------|
| prod | `fprtool-prod` | `https://fpr-mcp-gateway-ghntgmtwjb.gateway.bedrock-agentcore.ap-southeast-1.amazonaws.com` |
| stg | `fprtool-fpr` | `https://fpr-cortex-sg-ruypqkcdov.gateway.bedrock-agentcore.ap-southeast-1.amazonaws.com` |

`operation_name` is identical across envs. Only the prefix differs. Default prod — use stg only when user explicitly says "staging" / "stg" / "测试环境".

## Error Handling

| Code | Action | Retry |
|------|--------|-------|
| 401 | re-auth → retry | 1 |
| 400 | re-search schema → retry | 1 |
| 429 / 503 | backoff 1s → 3s → 9s | 3 |
| 403 / 500 | report to user | 0 |

Retry silently for 401/400/429/503. Full decision tree → [`error-classification.md`](references/error-classification.md).

## Version

Current 2.9.0. Check: `curl -sf https://raw.githubusercontent.com/lehan822/fpr-cortex/main/VERSION`
