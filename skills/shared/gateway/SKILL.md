---
name: fpr-shared
version: 2.9.0
description: "Flight Pricing & Revenue shared layer: auth, calling conventions, common parameter standards. Covers both local agents and AgentCore agents."
category: shared
---

# fpr-shared — MCP Gateway Calling Convention

> Shared layer for ALL FPR tools: how to authenticate, build the request envelope, and call the Gateway.
> It does NOT know about specific tools or their parameters — that's each domain skill's job.

```bash
# Every local call: auth gate → then tools/call
python3 ~/.fpr/fpr-auth.py refresh <env>
curl -s -X POST "{gateway_endpoint}/mcp" \
  -H "Authorization: Bearer {access_token}" -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","id":"1",
       "params":{"name":"{tool_prefix}___{operation_name}",
                 "arguments":{"data":{...},"context":{"authServiceToken":"{id_token}"},"clientInterface":"DESKTOP","fields":[]}}}'
```

## Prerequisites — Read Before Executing

**CRITICAL — read the file for your situation. None optional:**

1. **Any local MCP call** → MUST read [`auth.md`](references/auth.md) (auth gate, token model, bootstrap)
2. **Picking env / endpoints / prefixes** → MUST read [`environment.md`](references/environment.md)
3. **Building the JSON-RPC request, pagination, response shape** → MUST read [`gateway-protocol.md`](references/gateway-protocol.md)
4. **Any error after a call** → MUST read [`error-classification.md`](references/error-classification.md)
5. **AgentCore deploy/infra** → read [`agentcore-infra-setup.md`](../../../docs/agentcore-infra-setup.md)

## Agent Type Detection

| Signal | Agent Type | Auth |
|--------|-----------|------|
| Copilot CLI / Cursor / Claude Code | **Local** | PKCE tokens via `fpr-auth.py` → [`auth.md`](references/auth.md) |
| AgentCore (ECS/Lambda), has IAM role | **AgentCore** | M2M token auto-managed by runtime |

## Call Flow — schema-first (always)

**Every tool call follows the same 3 steps. No exceptions, no "direct call" shortcut.**

```
1. SEARCH schema   → x_amz_bedrock_agentcore_search(operation_name)  → get inputSchema
2. BUILD request   → fill arguments.data{} from the schema; wrap in envelope
3. CALL            → auth gate, then tools/call with {tool_prefix}___{operation_name}
```

- **Step 1 is mandatory.** Searching by exact tool name has ~100% hit rate and returns the authoritative `inputSchema`. The schema — not any skill file — is the source of truth for parameters.
- **Never call `tools/list`** — it dumps all 60+ tool schemas (~5000 tokens). Always search by name (~900 tokens, top-3).
- **Cache within a session** — once you've searched an operation's schema, reuse it; don't re-search.

### Role split

| Component | Responsibility |
|-----------|----------------|
| **Domain skill routing** | User intent → which `operation_name` |
| **Domain skill notes** | Business knowledge schema can't give: enums, normalization, gotchas |
| **Semantic search (this layer)** | Schema loader: authoritative `inputSchema` for the selected tool |
| **fpr-shared (this file)** | Auth, envelope, tool-name prefix, error handling — common to all tools |

### Search request

```json
{"jsonrpc":"2.0","method":"tools/call","id":"1",
 "params":{"name":"x_amz_bedrock_agentcore_search","arguments":{"query":"<operation_name>"}}}
```

Use the matching top-3 result's `inputSchema` to fill parameters. Full protocol → [`gateway-protocol.md`](references/gateway-protocol.md).

## Request Envelope

Tool name: `{tool_prefix}___{operation_name}` (prefix per env → [`environment.md`](references/environment.md)).

Arguments are wrapped:

| Field | Value |
|-------|-------|
| `data` | the operation's params (filled from schema) |
| `context.authServiceToken` | user id_token (local: from `auth.json`; AgentCore: passed from caller) |
| `clientInterface` | `"DESKTOP"` |
| `fields` | `[]` unless schema says otherwise |

## Auth Gate

Before any local call: `python3 ~/.fpr/fpr-auth.py refresh <env>` → proceed on exit 0 only.
All commands, token model, bootstrap → [`auth.md`](references/auth.md). AgentCore skips this (runtime handles it).

## Error Handling

After **every** `tools/call`, extract the real error from the response (don't pass through bare HTTP codes).

| HTTP | Detect | Action | Retries |
|------|--------|--------|---------|
| 401 | "Unauthorized", "ExpiredToken" | `fpr-auth.py refresh` → retry | 1 |
| 400 | "validation", "ArrayIndexOutOfBounds" | re-search schema → rebuild → retry | 1 |
| 429 / 503 | "Rate exceeded", "temporarily" | backoff 1s→3s→9s | 3 |
| 403 | "Forbidden" | report to user, no retry | 0 |
| 500 | "Internal Server Error" | report to user, no retry | 0 |

Retry silently for 401/400/429/503; never for 403/500. Full decision tree & where to find error text → [`error-classification.md`](references/error-classification.md).

## Version Check

**Current: 2.9.0** — on first load:

```bash
curl -sf https://raw.githubusercontent.com/lehan822/fpr-cortex/main/VERSION
```

If remote is newer, tell the user: "Run `npx skills update -g` to update."
