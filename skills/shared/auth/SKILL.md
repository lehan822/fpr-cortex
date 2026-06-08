---
name: fpr-shared
version: 2.6.0
description: "Flight Pricing & Revenue shared layer: auth, calling conventions, common parameter standards. Required for LOCAL MCP only — AgentCore agents skip this."
category: shared
---

# fpr-shared — Local MCP Calling Convention

> **Scope:** This skill applies ONLY to local agents (Copilot CLI, Cursor, Claude Code, etc.) connecting via local MCP server. AgentCore agents do NOT need this — Gateway handles auth and request formatting automatically.

## Quick Reference

| What | Where |
|------|-------|
| PKCE login flow + script | `references/pkce-login.md` |
| Gateway protocol (MCP JSON-RPC) | `references/gateway-protocol.md` |

## Calling Convention (Local MCP)

- **Tool name prefix:** `fprtool-backend___<operationId>` (e.g. `fprtool-backend___load_autopilot_rules`)
- **Params:** wrapped in `data:{}` envelope with `context.authServiceToken`, `clientInterface`, `fields`
- **Auth:** dual token (id_token + access_token from PKCE login)

## Authentication (Dual Token Architecture)

Every request uses **two tokens**:

| Token | Owner | Stored In |
|-------|--------|--------|
| User id_token | **User** | `~/.fpr/auth.json` → `body.context.authServiceToken` |
| M2M access_token | **Agent/Gateway** | `~/.fpr/auth.json` → `Authorization` header |

### Token Check Order

1. `~/.fpr/auth.json` does not exist → run PKCE login (see `references/pkce-login.md`)
2. `expires_at` > now → use tokens directly
3. `expires_at` < now + `refresh_token` exists → try refresh (see `references/pkce-login.md`)
4. refresh fails → run PKCE login again

### M2M Token

- Preconfigured by AgentCore Gateway infrastructure
- Automatically obtained and refreshed; transparent to user
- **Never ask the user for client_id or client_secret**

## Environment Configuration

| Environment | Gateway Endpoint | Backend | Client ID |
|-------------|-----------------|---------|-----------|
| stg (sstg) | `https://fpr-lehan-jwt-gw-z6tsij9aib.gateway.bedrock-agentcore.ap-southeast-1.amazonaws.com` | `tool-api.fpr.staging-traveloka.com` | `38taf824vlbfba3lta3eitcuhi` |
| prod | TBD | `tool-api.fpr.traveloka.com` | `i01t804ups4dme8p1kfoat8jb` |

> fstg (flight staging, dev) is NOT connected to Gateway — use direct curl for dev testing.

## Gateway — How to Call Tools

⚠️ Tool names are prefixed: `fprtool-backend___<operationId>`

```bash
curl -s -X POST "{gateway_endpoint}/mcp" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {access_token}" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "id": "1",
    "params": {
      "name": "fprtool-backend___<operationId>",
      "arguments": {
        "data": { ... },
        "context": { "authServiceToken": "<id_token>" },
        "clientInterface": "DESKTOP",
        "fields": []
      }
    }
  }'
```

For full protocol details (pagination, tool discovery, response format), see `references/gateway-protocol.md`.

## Error Handling

| HTTP Code | Meaning | Agent Action |
|-----------|---------|-------------|
| 401 | User token expired | Run PKCE login again |
| 403 | Insufficient permissions | Inform user: contact FPR team |
| 404 | Operation not found | Check operation name (needs `fprtool-backend___` prefix) |
| 429 | Rate limited | Retry with backoff (5s, 10s, 20s) |
| 500 | Backend error | Report error, suggest retry |

## Version Check

**Current: 2.5.0** — On first load, check:

```bash
curl -sf https://raw.githubusercontent.com/lehan822/fpr-cortex/main/VERSION
```

If remote > 2.5.0, inform user: "Run `npx skills update -g` to update."
