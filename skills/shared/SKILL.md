---
name: fpr-shared
version: 2.0.0
description: "Flight Pricing & Revenue shared layer: AgentCore Gateway auth (M2M + user token passthrough), environment config, common parameter standards. Read this FIRST before using any fpr-* skill."
---

# fpr-shared — Auth, Gateway, Common Standards

**Read this FIRST before using any domain skill (fpr-pricing, fpr-supply, etc.)**

## Authentication (Dual Token)

Two tokens are used per request:

| Token | Location | Purpose |
|-------|----------|---------|
| M2M access_token | `Authorization` header | Proves agent is registered (Gateway validates) |
| User id_token | `body.context.authServiceToken` | Identifies which user initiated the request |

### M2M Token (Agent Identity)

```
POST https://m2m-auth.ath.traveloka.com/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&client_id=<ID>&client_secret=<SECRET>&audience=<AUDIENCE>
```

- Credentials stored at `~/.fpr/credentials.json`
- Auto-refresh when `expires_at` < now
- Each agent has its own client_id (auditable)

### User Token (User Identity)

- Obtained via Cognito PKCE flow (first-time browser login)
- Stored alongside M2M credentials
- Passed in request body — Gateway does NOT strip body fields

### Setup

```bash
# First time: register M2M credentials
fpr-cortex auth setup --client-id <ID> --client-secret <SECRET>

# First time: user login (opens browser)
fpr-cortex auth login
```

## Gateway Configuration

| Environment | Gateway Endpoint | M2M Issuer |
|-------------|-----------------|------------|
| staging | `https://agentcore-gw.staging-traveloka.com` | `https://m2m-auth.ath.staging-traveloka.com` |
| production | `https://agentcore-gw.traveloka.com` | `https://m2m-auth.ath.traveloka.com` |

### Request Format

```json
POST {gateway_endpoint}/{domain}/{operation}
Authorization: Bearer {m2m_access_token}
Content-Type: application/json

{
  "context": {
    "authServiceToken": "{user_id_token}"
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
| 401 | M2M token expired/invalid | Clear cache → re-auth |
| 403 | Scope insufficient | Report to user: "需要额外权限" |
| 404 | Operation not found | Check operation name spelling |
| 429 | Rate limited | Retry with backoff |
| 500 | Backend error | Report error, suggest retry |

## Environment Switching

Default: staging. Switch via:
- Flag: `--env production`
- Env var: `export FPR_ENV=production`
