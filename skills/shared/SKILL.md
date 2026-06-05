---
name: fpr-shared
version: 2.1.0
description: "Flight Pricing & Revenue shared layer: AgentCore Gateway auth, environment config, common parameter standards. Read this FIRST before using any fpr-* skill."
---

# fpr-shared — Auth, Gateway, Common Standards

**Read this FIRST before using any domain skill (fpr-pricing, fpr-supply, etc.)**

## Authentication

### For Users (You Handle This)

User authenticates via **browser login** — like lark-cli's `config init`:

```bash
fpr-cortex auth login
```

This opens the browser → user logs in via Traveloka SSO → token saved locally.

- Token stored at `~/.fpr/auth.json`
- Auto-refreshed on expiry (PKCE refresh flow)
- **No M2M credentials needed from users** — M2M is pre-configured on the Gateway side

If `~/.fpr/auth.json` doesn't exist or token is expired, prompt:

> 🔐 需要登录。运行 `fpr-cortex auth login` 或我帮你打开登录页面？

**Never ask users for client_id, client_secret, or M2M credentials.** Those are Gateway infrastructure, not user concerns.

### How It Works (Background)

```
User token (from browser login)
    ↓
Agent puts in body.context.authServiceToken
    ↓
AgentCore Gateway adds M2M header automatically
    ↓
fprtool-backend validates user token → returns data
```

| Token | Who manages | Where |
|-------|------------|-------|
| User id_token | User (browser login) | `body.context.authServiceToken` |
| M2M access_token | Gateway (pre-configured) | `Authorization` header (auto-injected) |

## Gateway Configuration

| Environment | Gateway Endpoint |
|-------------|-----------------|
| staging | `https://agentcore-gw.staging-traveloka.com` |
| production | `https://agentcore-gw.traveloka.com` |

Default: staging. Switch via `--env production` or `export FPR_ENV=production`.

### Request Format

```json
POST {gateway_endpoint}/{domain}/{operation}
Content-Type: application/json

{
  "context": {
    "authServiceToken": "{user_id_token_from_local_auth}"
  },
  "params": {
    "country": "TH",
    "currency": "THB"
  }
}
```

## Common Parameter Standards

| Parameter | Format | Examples |
|-----------|--------|----------|
| country | ISO 3166-1 alpha-2 | ID, TH, VN, MY, SG, AU |
| currency | ISO 4217 | IDR, THB, VND, MYR, SGD, AUD |
| profileGroup | = country code | TH, ID, VN |
| airlineId | IATA 2-letter | GA, QZ, VJ, TG |
| fulfillmentId | Internal ID | (varies) |

## Error Handling

| HTTP Code | Meaning | Agent Action |
|-----------|---------|-------------|
| 401 | User token expired | Prompt: `fpr-cortex auth login` to re-authenticate |
| 403 | Insufficient permissions | Tell user: "需要额外权限，请联系 FPR team" |
| 404 | Operation not found | Check operation name in domain skill |
| 429 | Rate limited | Retry with backoff (5s, 10s, 20s) |
| 500 | Backend error | Report error, suggest retry |

## Version Check

**Current installed version: 2.1.0**

When fpr-shared is first loaded in a session, check for updates:

```bash
curl -sf https://raw.githubusercontent.com/lehan822/fpr-cortex/main/VERSION
```

If remote version > `2.1.0`, inform user after completing their request:

> ℹ️ FPR Skills 有新版本 (vX.Y.Z)。运行 `npx skills update -g` 更新。

Only check once per session. Do not block the user's current request.
