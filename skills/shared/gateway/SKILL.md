---
name: fpr-shared
version: 2.9.0
description: "Flight Pricing & Revenue shared layer: auth, calling conventions, common parameter standards. Covers both local agents and AgentCore agents."
category: shared
---

# fpr-shared — MCP Gateway Calling Convention

## Agent Type Detection

| Signal | Agent Type | Auth |
|--------|-----------|------|
| Running in Copilot CLI / Cursor / Claude Code | **Local** | PKCE tokens from `~/.fpr/auth.json` |
| Running on AgentCore (ECS/Lambda), has IAM role | **AgentCore** | M2M token auto-managed by runtime |

## Quick Reference

| What | Where |
|------|-------|
| PKCE login flow + script (local only) | `references/pkce-login.md` |
| Gateway protocol (MCP JSON-RPC) | `references/gateway-protocol.md` |
| AgentCore infra setup guide | `references/agentcore-infra-setup.md` |

## Tool Invocation

All tools are called via MCP Gateway. Tool name format:

```
{target_prefix}___{operation_name}
```

| Environment | Target Prefix | Example |
|-------------|--------------|---------|
| stg (all agents) | `fprtool-fpr` | `fprtool-fpr___load_autopilot_rules` |
| prod | `fprtool-prod` | `fprtool-prod___load_autopilot_rules` |

> The `operation_name` is the same across environments. Only the prefix differs based on which Gateway target you connect to.

## Request Format (Local MCP)

- **Params:** wrapped in `data:{}` envelope with `context.authServiceToken`, `clientInterface`, `fields`
- **Auth:** dual token (id_token + access_token from PKCE login)

## Authentication

### Local Agent (Copilot CLI / Cursor / Claude Code)

Every request uses **two tokens**:

| Token | Owner | Stored In |
|-------|--------|--------|
| User id_token | **User** | `~/.fpr/auth.json` → `body.context.authServiceToken` |
| access_token | **User** | `~/.fpr/auth.json` → `Authorization` header |

### AgentCore Agent (ECS / Lambda)

| Token | Owner | Source |
|-------|--------|--------|
| User id_token | **End user** | Passed in from caller (Lark bot / Web) → `body.context.authServiceToken` |
| M2M token | **AgentCore runtime** | Auto-managed by IAM role, transparent to agent code |

**AgentCore agents do NOT run PKCE login.** The runtime handles Gateway auth via IAM/SigV4. Agent code only needs to:
1. Receive user's `id_token` from the upstream caller
2. Pass it through in `context.authServiceToken`
3. Call the gateway endpoint (from env var `GATEWAY_ENDPOINT`)

### Token Check Order (Local Agent Only)

1. `~/.fpr/auth.json` does not exist → run PKCE login (see `references/pkce-login.md`)
2. `expires_at` > now → use tokens directly
3. `expires_at` < now + `refresh_token` exists → try refresh (see `references/pkce-login.md`)
4. refresh fails → run PKCE login again

### M2M Token (AgentCore Only)

- Preconfigured by AgentCore runtime IAM role
- Automatically obtained and refreshed; transparent to agent code
- **Never ask the user for client_id or client_secret**
- Agent code simply calls the gateway — runtime handles auth headers

## Environment Configuration

| Environment | Gateway Endpoint | Backend | PKCE Client ID (local) |
|-------------|-----------------|---------|-----------|
| stg (sstg) | `https://fpr-cortex-sg-ruypqkcdov.gateway.bedrock-agentcore.ap-southeast-1.amazonaws.com` | `tool-api.fpr.staging-traveloka.com` | `38taf824vlbfba3lta3eitcuhi` |
| prod | `https://fpr-mcp-gateway-ghntgmtwjb.gateway.bedrock-agentcore.ap-southeast-1.amazonaws.com` | `tool-api.fpr.traveloka.com` | `i01t804ups4dme8p1kfoat8jb` |

> fstg (flight staging, dev) is NOT connected to Gateway — use direct curl for dev testing.

### AgentCore Agent Environment Resolution

Agent determines environment from deployment config:

```python
# Agent code reads from env var (set at deploy time)
GATEWAY_ENDPOINT = os.environ["GATEWAY_ENDPOINT"]
# stg deploy → stg gateway URL
# prod deploy → prod gateway URL
```

No login, no token management — just call the endpoint.

## Tool Selection & Schema Loading

### Flow

1. **Skill selects tool** — Read domain skill routing guide → determine which operation to call
2. **Search loads schema** — Call `x_amz_bedrock_agentcore_search` with the **tool name** → get inputSchema (field names, types, enums)
3. **Fill parameters** — Combine skill knowledge (gotchas, normalization) + schema (exact fields) → build request
4. **Call tool** via `tools/call`

### Role Split

| Component | Responsibility |
|-----------|---------------|
| **Skill routing guide** | Tool selection: user intent → operation name |
| **Skill param notes** | Domain knowledge: gotchas, enums, normalization, workflows |
| **Semantic Search** | Schema loader: fetch inputSchema for the selected tool |

### Why This Order

- Skill routing is **deterministic** (51 tools, covers 100% of gateway)
- Search is **probabilistic** (returns top-N, may miss niche tools)
- Search is reliable as a **schema loader** when queried by exact tool name (100% hit rate)
- For complex operations (update/create with nested fields), schema is essential — skill cannot document all fields

### Search Request (Schema Loading)

After skill selects the tool, load its schema:

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "id": "1",
  "params": {
    "name": "x_amz_bedrock_agentcore_search",
    "arguments": {"query": "<selected_tool_name>"}
  }
}
```

From the response, find the matching tool in the top 3 results and use its `inputSchema` to fill parameters.

### When to Skip Search

For **simple GET operations** where the skill already documents all required fields (e.g. `load_autopilot_rules` → `originCountry, profileGroup, airlineId`), you may call directly without search. Use search when:
- The operation has many/nested fields (update, create operations)
- You're unsure about exact field names or structure
- The first call failed due to missing/wrong parameters (fallback)

## Gateway — How to Call Tools

⚠️ Tool names use target prefix: `fprtool-fpr___<operationId>`

```bash
curl -s -X POST "{gateway_endpoint}/mcp" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {access_token}" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "id": "1",
    "params": {
      "name": "fprtool-fpr___<operationId>",
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

## Environment Routing

**Default: prod.** Unless user explicitly says "staging" / "stg" / "测试环境", always use prod gateway.

### Auth File: `~/.fpr/auth.json`

Single file stores tokens for ALL environments:

```json
{
  "active": "prod",
  "environments": {
    "prod": {
      "id_token": "...",
      "access_token": "...",
      "refresh_token": "...",
      "expires_at": 1781264126688,
      "gateway": "https://fpr-mcp-gateway-ghntgmtwjb.gateway.bedrock-agentcore.ap-southeast-1.amazonaws.com",
      "tool_prefix": "fprtool-prod"
    },
    "stg": {
      "id_token": "...",
      "access_token": "...",
      "refresh_token": "...",
      "expires_at": 1781255897391,
      "gateway": "https://fpr-cortex-sg-ruypqkcdov.gateway.bedrock-agentcore.ap-southeast-1.amazonaws.com",
      "tool_prefix": "fprtool-fpr"
    }
  }
}
```

### Token Resolution

1. Determine env from user intent (default: `prod`)
2. Read `environments[env]`
3. If `expires_at` < now → try refresh, else PKCE login for that env
4. Use `gateway` and `tool_prefix` from selected env
5. `active` field tracks last-used env (informational only)

### Switching Environments

No re-login needed if both tokens are valid. Just read from the correct env key.

```bash
# Read prod token
node -e "const a=JSON.parse(require('fs').readFileSync(process.env.HOME+'/.fpr/auth.json'));console.log(a.environments.prod.access_token)"

# Read stg token  
node -e "const a=JSON.parse(require('fs').readFileSync(process.env.HOME+'/.fpr/auth.json'));console.log(a.environments.stg.access_token)"
```

## Error Handling

| HTTP Code | Meaning | Agent Action |
|-----------|---------|-------------|
| 401 | User token expired | Run PKCE login again |
| 403 | Insufficient permissions | Inform user: contact FPR team |
| 404 | Operation not found | Check operation name (needs `fprtool-fpr___` prefix) |
| 429 | Rate limited | Retry with backoff (5s, 10s, 20s) |
| 500 | Backend error | Report error, suggest retry |

## Version Check

**Current: 2.6.0** — On first load, check:

```bash
curl -sf https://raw.githubusercontent.com/lehan822/fpr-cortex/main/VERSION
```

If remote > 2.5.0, inform user: "Run `npx skills update -g` to update."
