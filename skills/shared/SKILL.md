---
name: fpr-shared
version: 2.5.0
description: "Flight Pricing & Revenue shared layer: AgentCore Gateway auth, environment config, common parameter standards. Read this FIRST before using any fpr-* skill."
---

# fpr-shared — Auth, Gateway, Common Standards

**Read this FIRST before using any domain skill (fpr-pricing, fpr-supply, etc.)**

## Authentication (Dual Token Architecture)

Every request uses **two tokens** — one from the user, one from the agent:

| Token | 谁负责 | 获取方式 | 放在哪 |
|-------|--------|---------|--------|
| User id_token | **用户** | 浏览器 SSO 登录（见下方流程） | `body.context.authServiceToken` |
| M2M access_token | **Agent/Gateway** | Client Credentials Grant (预配置) | `Authorization` header (自动注入) |

### M2M Token（Agent 负责，用户不碰）

- 由 AgentCore Gateway 基础设施预配置
- Agent 自动获取和刷新，对用户完全透明
- **永远不要向用户询问 client_id 或 client_secret**

### User Token — PKCE 登录流程

**当 `~/.fpr/auth.json` 不存在或 `expires_at` < 当前时间时，执行以下登录流程：**

1. 询问用户要用哪个环境（staging / production）
2. 用 inline Node.js 脚本执行 PKCE OAuth 流程（见下方）
3. 登录成功后继续用户原来的查询

#### 环境配置

| 环境 | Authorize URL | Token URL | Client ID |
|------|--------------|-----------|-----------|
| staging | `https://internal-id.ath.staging-traveloka.com/oauth2/authorize` | `https://internal-id.ath.staging-traveloka.com/oauth2/token` | `38taf824vlbfba3lta3eitcuhi` |
| production | `https://internal-id.ath.traveloka.com/oauth2/authorize` | `https://internal-id.ath.traveloka.com/oauth2/token` | `i01t804ups4dme8p1kfoat8jb` |

#### PKCE 登录步骤

用 bash async mode 执行以下 inline Node.js 脚本：

```javascript
// 替换 AUTHORIZE_URL, TOKEN_URL, CLIENT_ID 为上表对应环境的值
const http = require('http');
const https = require('https');
const crypto = require('crypto');
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const url = require('url');

const AUTHORIZE_URL = '<from table above>';
const TOKEN_URL = '<from table above>';
const CLIENT_ID = '<from table above>';
const PORT = 18999;
const REDIRECT_URI = `http://localhost:${PORT}/callback`;
const AUTH_FILE = path.join(process.env.HOME, '.fpr', 'auth.json');

const b64url = buf => buf.toString('base64').replace(/\+/g,'-').replace(/\//g,'_').replace(/=/g,'');
const verifier = b64url(crypto.randomBytes(32));
const challenge = b64url(crypto.createHash('sha256').update(verifier).digest());
const state = b64url(crypto.randomBytes(16));

const authUrl = `${AUTHORIZE_URL}?` + new URLSearchParams({
  response_type: 'code', client_id: CLIENT_ID, redirect_uri: REDIRECT_URI,
  scope: 'openid email profile', state, code_challenge: challenge, code_challenge_method: 'S256'
}).toString();

const server = http.createServer(async (req, res) => {
  const p = url.parse(req.url, true);
  if (p.pathname !== '/callback') return res.writeHead(404).end();
  if (p.query.error) { console.error('❌', p.query.error); process.exit(1); }
  if (p.query.state !== state) { console.error('❌ state mismatch'); process.exit(1); }

  const body = new URLSearchParams({
    grant_type:'authorization_code', client_id:CLIENT_ID, code:p.query.code,
    redirect_uri:REDIRECT_URI, code_verifier:verifier
  }).toString();

  const u = new URL(TOKEN_URL);
  const r = https.request({hostname:u.hostname,path:u.pathname,method:'POST',
    headers:{'Content-Type':'application/x-www-form-urlencoded','Content-Length':Buffer.byteLength(body)}
  }, tr => {
    let d=''; tr.on('data',c=>d+=c); tr.on('end',()=>{
      if(tr.statusCode!==200){console.error('❌ token exchange failed:',d);process.exit(1);}
      const t=JSON.parse(d);
      fs.mkdirSync(path.dirname(AUTH_FILE),{recursive:true});
      fs.writeFileSync(AUTH_FILE,JSON.stringify({env:process.env.FPR_ENV||'stg',
        id_token:t.id_token, access_token:t.access_token, refresh_token:t.refresh_token,
        expires_at:Date.now()+(t.expires_in*1000), obtained_at:new Date().toISOString()},null,2));
      res.writeHead(200,{'Content-Type':'text/html'}).end(
        '<h2>✅ Login successful!</h2><p>You can close this tab.</p>');
      console.log('✅ Login successful. Token saved to ~/.fpr/auth.json');
      server.close(()=>process.exit(0));
    });
  });
  r.write(body); r.end();
});

server.listen(PORT, () => {
  console.log('🔐 Opening browser for login...');
  exec((process.platform==='darwin'?'open':'xdg-open')+` "${authUrl}"`);
});
setTimeout(()=>{console.error('⏰ Timeout');process.exit(1);},120000);
```

#### 读取 Token

登录完成后，从 `~/.fpr/auth.json` 读取两个 token：

```bash
# 检查是否过期
node -e "const a=JSON.parse(require('fs').readFileSync(process.env.HOME+'/.fpr/auth.json'));
  if(a.expires_at<Date.now()){console.log('EXPIRED');process.exit(1);}
  console.log('OK');"

# access_token (Gateway auth header)
node -e "console.log(JSON.parse(require('fs').readFileSync(process.env.HOME+'/.fpr/auth.json')).access_token)"

# id_token (user identity in body)
node -e "console.log(JSON.parse(require('fs').readFileSync(process.env.HOME+'/.fpr/auth.json')).id_token)"
```

#### Token 刷新

当 `expires_at` < 当前时间但 `refresh_token` 存在时，**先尝试刷新，不要重新登录：**

```bash
# 读取环境配置
ENV=$(cat ~/.fpr/auth.json | node -e "process.stdin.on('data',d=>console.log(JSON.parse(d).env||'stg'))")
REFRESH_TOKEN=$(cat ~/.fpr/auth.json | node -e "process.stdin.on('data',d=>console.log(JSON.parse(d).refresh_token))")

# stg: TOKEN_URL=https://internal-id.ath.staging-traveloka.com/oauth2/token CLIENT_ID=38taf824vlbfba3lta3eitcuhi
# prod: TOKEN_URL=https://internal-id.ath.traveloka.com/oauth2/token CLIENT_ID=i01t804ups4dme8p1kfoat8jb

curl -s -X POST "$TOKEN_URL" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=refresh_token&client_id=$CLIENT_ID&refresh_token=$REFRESH_TOKEN"
```

成功返回新 tokens → 更新 `~/.fpr/auth.json`（同结构）。
如果 refresh 失败（400/401）→ refresh_token 也过期了 → 重新执行 PKCE 登录流程。

#### 检查顺序

1. `~/.fpr/auth.json` 不存在 → PKCE 登录
2. `expires_at` > now → 直接用 `id_token`
3. `expires_at` < now + `refresh_token` 存在 → 尝试 refresh
4. refresh 失败 → PKCE 登录

## Gateway Configuration

| Environment | Gateway Endpoint |
|-------------|-----------------|
| staging | `https://fpr-lehan-jwt-gw-z6tsij9aib.gateway.bedrock-agentcore.ap-southeast-1.amazonaws.com` |
| production | TBD (pending deployment) |

### Tool Discovery (tools/list with pagination)

Gateway paginates tools at **30 per page**. Always handle `nextCursor`:

```bash
# Page 1
curl -s -X POST "{gateway_endpoint}/mcp" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# If response has nextCursor, fetch next page:
curl -s -X POST "{gateway_endpoint}/mcp" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{"cursor":"<nextCursor>"}}'
```

Total tools: **55** across 2 pages. Always paginate until `nextCursor` is absent.

### Tool Naming Convention

⚠️ **Gateway prefixes tool names with target name:** `fprtool-backend___<operationId>`

When calling `tools/call`, use the **full prefixed name**:
- ✅ `fprtool-backend___load_commission_incentive_rules`
- ❌ `load_commission_incentive_rules` (will fail with "tool not found")

### Request Format (MCP JSON-RPC)

Gateway uses MCP protocol. All requests go to the `/mcp` endpoint.

⚠️ **Traveloka Request Envelope:** All tool parameters MUST be wrapped inside `data`. The Gateway only forwards fields declared in the schema. The four required envelope fields are:

| Field | Required | Description |
|-------|----------|-------------|
| `data` | ✅ | Contains all tool-specific parameters |
| `context` | ✅ | Must include `authServiceToken` (id_token) |
| `clientInterface` | ✅ | Always `"DESKTOP"` |
| `fields` | ✅ | Always `[]` |

```bash
curl -s -X POST "{gateway_endpoint}/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer {access_token_from_auth_json}" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "id": "1",
    "params": {
      "name": "fprtool-backend___<operationId>",
      "arguments": {
        "data": {
          "<param1>": "<value1>",
          "<param2>": "<value2>"
        },
        "context": {
          "authServiceToken": "<id_token_from_auth_json>"
        },
        "clientInterface": "DESKTOP",
        "fields": []
      }
    }
  }'
```

**Example — query GA commission rules (staging):**

```bash
curl -s -X POST "https://fpr-lehan-jwt-gw-z6tsij9aib.gateway.bedrock-agentcore.ap-southeast-1.amazonaws.com/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $(cat ~/.fpr/auth.json | node -e \"process.stdin.on('data',d=>console.log(JSON.parse(d).access_token))\")" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "id": "1",
    "params": {
      "name": "fprtool-backend___load_commission_incentive_rules",
      "arguments": {
        "data": {
          "airline": "GA"
        },
        "context": {
          "authServiceToken": "'$(cat ~/.fpr/auth.json | node -e "process.stdin.on('data',d=>console.log(JSON.parse(d).id_token))")'"
        },
        "clientInterface": "DESKTOP",
        "fields": []
      }
    }
  }'
```

**Response format:**
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": {
    "content": [{ "type": "text", "text": "..." }]
  }
}
```

**Key points:**
- `Authorization` header → `access_token` (Cognito, for Gateway auth)
- `arguments.context.authServiceToken` → `id_token` (for fprtool-backend user identity)
- `arguments.data` → all tool-specific params go inside `data` wrapper
- `name` = `fprtool-backend___<operationId>` (with target prefix)
- All operations use `method: "tools/call"`

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
| 401 | User token expired | 重新执行 PKCE 登录流程 |
| 403 | Insufficient permissions | 告知用户："需要额外权限，请联系 FPR team" |
| 404 | Operation not found | 检查 operation name |
| 429 | Rate limited | Retry with backoff (5s, 10s, 20s) |
| 500 | Backend error | Report error, suggest retry |

## Version Check

**Current installed version: 2.5.0**

When fpr-shared is first loaded in a session, check for updates:

```bash
curl -sf https://raw.githubusercontent.com/lehan822/fpr-cortex/main/VERSION
```

If remote version > `2.5.0`, inform user after completing their request:

> ℹ️ FPR Skills 有新版本 (vX.Y.Z)。运行 `npx skills update -g` 更新。
