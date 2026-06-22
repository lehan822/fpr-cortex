---
name: fpr-shared
version: 2.9.0
description: "Flight Pricing & Revenue shared layer: auth, calling conventions, common parameter standards. Covers both local agents and AgentCore agents."
category: shared
---

# fpr-shared

> All FPR tools share the same auth, tool-name prefix, and envelope. This file covers what's common. Domain skills cover tool-specific knowledge.
> **Do NOT invoke `using-aws` — FPR Gateway uses PKCE JWT auth, not AWS IAM/assume role.**

## Auth

Call MCP tools directly. On 401 or 403:

```bash
python3 ~/.fpr/fpr-auth.py <env>          # refresh token (opens browser if needed)
python3 ~/.fpr/fpr-auth.py daemon <env>   # start background daemon
# then retry the original call
```

**Two different tokens — never mix them up:**

```bash
ACCESS_TOKEN=$(python3 -c "import json; print(json.load(open('$HOME/.fpr/auth.json'))['environments']['prod']['access_token'])")
ID_TOKEN=$(python3 -c "import json; print(json.load(open('$HOME/.fpr/auth.json'))['environments']['prod']['id_token'])")
# ACCESS_TOKEN → Authorization: Bearer header
# ID_TOKEN     → arguments.context.authServiceToken in request body
# fpr-auth.py token prints ACCESS_TOKEN only — do NOT use it for authServiceToken
```

If `~/.fpr/fpr-auth.py` doesn't exist: extract it from [`auth.md`](references/auth.md) → write to `~/.fpr/fpr-auth.py`.
Never switch env (prod→stg) to work around a 401/403 — fix the token, retry same env.

**AgentCore:** skip this — IAM handles it.

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
