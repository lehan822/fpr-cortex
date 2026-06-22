---
name: fpr-shared
version: 2.9.0
description: "Flight Pricing & Revenue shared layer: auth, calling conventions, common parameter standards. Covers both local agents and AgentCore agents."
category: shared
---

# fpr-shared

> All FPR tools share the same auth, tool-name prefix, and envelope. This file covers what's common. Domain skills cover tool-specific knowledge.

## Before any call

**Local agent:** run auth first, always:

```bash
# First-time: copy the auth script
cp ~/.agents/skills/fpr-shared/scripts/fpr-auth.py ~/.fpr/

# Every call
python3 ~/.fpr/fpr-auth.py <env>
```

Proceed only on exit 0. Never probe gateway first, never read auth.json manually, never ask the user about auth.
All commands and token model → [`auth.md`](references/auth.md).

**AgentCore agents:** skip this — runtime handles auth via IAM.

## Call Flow — schema-first

```
1. SEARCH  → x_amz_bedrock_agentcore_search(operation_name) → get inputSchema
2. BUILD   → fill data{} from schema
3. CALL    → {prefix}___{operation_name}
```

Request wraps params in: `{data:{...}, context:{authServiceToken}, clientInterface:"DESKTOP", fields:[]}`

- Step 1 is mandatory. Search by name returns the authoritative inputSchema.
- Never call `tools/list` — 60+ tools, wastes tokens.
- Cache within session — don't re-search same operation.

Full JSON-RPC protocol, pagination, response shape → [`gateway-protocol.md`](references/gateway-protocol.md).

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

`operation_name` is identical across envs. Only the prefix differs.

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
