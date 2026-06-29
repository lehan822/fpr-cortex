---
name: fpr-tool-shared
version: 2.10.0
description: "[shared] Use when calling FPR Gateway/MCP tools, handling FPR auth errors, choosing prod/stg prefixes, or building JSON-RPC envelopes for local Flight Pricing & Revenue tools."
category: shared
---

# fpr-tool-shared

> All FPR tools share the same auth, tool-name prefix, and envelope. This file covers what's common. Domain skills cover tool-specific knowledge.
> **Do NOT invoke `using-aws` — FPR Gateway uses PKCE JWT auth, not AWS IAM/assume role.**

## Auth

Authoritative details: [`references/auth.md`](references/auth.md).

- `401` → auto auth with `python3 ~/.fpr/fpr-auth.py <env>`
- JSON-RPC `insufficient_scope` / code `-32002`, or switching login identity/scopes → force browser login with `python3 ~/.fpr/fpr-auth.py login <env>`
- `login <env>` binds `localhost:18999/callback` and opens Cognito; in Codex this usually requires escalated execution.
- For non-auth errors, do not run `fpr-auth.py`; classify the error and follow **Error Handling**.

**Two different tokens — never mix them up:**

```bash
ACCESS_TOKEN=$(python3 -c "import json; print(json.load(open('$HOME/.fpr/auth.json'))['environments']['prod']['access_token'])")
ID_TOKEN=$(python3 -c "import json; print(json.load(open('$HOME/.fpr/auth.json'))['environments']['prod']['id_token'])")
# ACCESS_TOKEN → Authorization: Bearer header
# ID_TOKEN     → arguments.context.authServiceToken in request body
# fpr-auth.py token prints ACCESS_TOKEN only — do NOT use it for authServiceToken
```

Never switch env (prod→stg) to work around a 401/403 — fix the token, retry same env.

**AgentCore:** skip this — IAM handles it.

## Call Flow — schema-first

Authoritative protocol details: [`references/gateway-protocol.md`](references/gateway-protocol.md).

Use bash/curl; do **not** register as an MCP server.

```
0. SELECT  → domain skill routes user intent to operation_name
1. SEARCH  → x_amz_bedrock_agentcore_search(operation_name) → get inputSchema
2. BUILD   → inputSchema.properties → data keys, normalized
3. CALL    → {prefix}___{operation_name} with data in envelope
```

Search call uses bare arguments. Tool calls use the envelope `{data, context:{authServiceToken}, clientInterface:"DESKTOP", fields:[]}`.

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

Authoritative details: [`references/error-classification.md`](references/error-classification.md).

- Extract the real error after every `tools/call`.
- Then follow the recovery table in `error-classification.md`.
- Never switch env (prod→stg) to work around errors — fix the root cause.

## Version

Current 2.10.0. Check: `curl -sf https://raw.githubusercontent.com/lehan822/fpr-cortex/main/VERSION`
