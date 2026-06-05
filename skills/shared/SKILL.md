---
name: fpr-shared
version: 2.2.0
description: "Flight Pricing & Revenue shared layer: AgentCore Gateway auth, environment config, common parameter standards. Read this FIRST before using any fpr-* skill."
---

# fpr-shared — Auth, Gateway, Common Standards

**Read this FIRST before using any domain skill (fpr-pricing, fpr-supply, etc.)**

## Authentication (Dual Token Architecture)

Every request uses **two tokens** — one from the user, one from the agent:

| Token | 谁负责 | 获取方式 | 放在哪 |
|-------|--------|---------|--------|
| User id_token | **用户** | 浏览器 SSO 登录 | `body.context.authServiceToken` |
| M2M access_token | **Agent/Gateway** | Client Credentials Grant (预配置) | `Authorization` header |

### User Token（用户负责）

用户通过浏览器登录获取身份 token。**Agent 直接执行登录脚本，自动弹出浏览器：**

```bash
# staging（默认）
node ~/.agents/skills/fpr-shared/auth/login.js

# production
node ~/.agents/skills/fpr-shared/auth/login.js --env prod
```

- 自动打开浏览器 → Traveloka SSO 登录 → token 存到 `~/.fpr/auth.json`
- 零依赖（只需 Node.js）
- Token 包含 env 标识（stg/prod），切环境需重新登录

**当 `~/.fpr/auth.json` 不存在或 token 过期时：**
1. 告知用户需要登录
2. 询问环境（staging / production）
3. 直接执行上面的命令（async mode，等待用户在浏览器完成登录）
4. 登录成功后继续原来的查询

### M2M Token（Agent 负责，用户不碰）

Agent 通过 Client Credentials Grant 自动获取 M2M token，证明自己是注册过的合法 agent。

- 由 AgentCore Gateway 基础设施预配置
- Agent 自动获取和刷新，对用户完全透明
- **永远不要向用户询问 client_id 或 client_secret**

### 请求流程

```
用户浏览器登录 → user token 存本地
                    ↓
Agent 组装请求:  body.context.authServiceToken = user_token
                    ↓
Agent 添加 M2M: Authorization: Bearer {m2m_token}  ← 自动，用户无感
                    ↓
AgentCore Gateway 验证 M2M → 放行
                    ↓
fprtool-backend 验证 user token → 返回该用户有权限的数据
```

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

**Current installed version: 2.2.0**

When fpr-shared is first loaded in a session, check for updates:

```bash
curl -sf https://raw.githubusercontent.com/lehan822/fpr-cortex/main/VERSION
```

If remote version > `2.2.0`, inform user after completing their request:

> ℹ️ FPR Skills 有新版本 (vX.Y.Z)。运行 `npx skills update -g` 更新。

Only check once per session. Do not block the user's current request.
