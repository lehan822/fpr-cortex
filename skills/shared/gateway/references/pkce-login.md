# PKCE Login Flow

## When to Trigger

- `~/.fpr/auth.json` does not exist
- `expires_at` < current time AND refresh fails

## Steps

1. Ask the user which environment to use (staging / production)
2. Run the PKCE OAuth flow using the script below
3. After login succeeds, continue the user's original request

## Environment URLs

| Environment | Authorize URL | Token URL | Client ID |
|------|--------------|-----------|-----------|
| staging | `https://internal-id.ath.staging-traveloka.com/oauth2/authorize` | `https://internal-id.ath.staging-traveloka.com/oauth2/token` | `38taf824vlbfba3lta3eitcuhi` |
| production | `https://internal-id.ath.traveloka.com/oauth2/authorize` | `https://internal-id.ath.traveloka.com/oauth2/token` | `i01t804ups4dme8p1kfoat8jb` |

## PKCE Login Script

Run in bash async mode:

```javascript
// Replace AUTHORIZE_URL, TOKEN_URL, and CLIENT_ID with the values for the corresponding environment in the table above
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
const PORT = 18999; // Fixed redirect port; must match Cognito callback registration
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
      let auth = {};
      try { auth = JSON.parse(fs.readFileSync(AUTH_FILE)); } catch(e) {}
      if (!auth.environments) auth.environments = {};
      const envName = process.env.FPR_ENV || 'stg';
      auth.active = envName;
      auth.environments[envName] = {
        id_token: t.id_token,
        access_token: t.access_token,
        refresh_token: t.refresh_token,
        expires_at: Date.now() + (t.expires_in * 1000),
        obtained_at: new Date().toISOString()
      };
      fs.mkdirSync(path.dirname(AUTH_FILE),{recursive:true});
      fs.writeFileSync(AUTH_FILE, JSON.stringify(auth, null, 2));
      res.writeHead(200,{'Content-Type':'text/html'}).end(
        '<h2>✅ Login successful!</h2><p>You can close this tab.</p>');
      console.log('✅ Login successful. Token saved to ~/.fpr/auth.json');
      server.close(()=>process.exit(0));
    });
  });
  r.write(body); r.end();
});

server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    console.error(`❌ Port ${PORT} is already in use. PKCE login requires the fixed callback URI http://localhost:${PORT}/callback.`);
    console.error('Please free the port and retry. Do NOT switch to another port, or Cognito will reject the redirect URI.');
    process.exit(1);
  }
  throw err;
});

server.listen(PORT, () => {
  console.log('🔐 Opening browser for login...');
  exec((process.platform==='darwin'?'open':'xdg-open')+` "${authUrl}"`);
});
setTimeout(()=>{console.error('⏰ Timeout');process.exit(1);},120000);
```

## Reading Tokens

```bash
# Check whether expired (prod example)
node -e "const a=JSON.parse(require('fs').readFileSync(process.env.HOME+'/.fpr/auth.json'));
  const env=a.environments.prod;
  if(!env||env.expires_at<Date.now()){console.log('EXPIRED');process.exit(1);}
  console.log('OK');"

# access_token (Gateway auth header, prod example)
node -e "console.log(JSON.parse(require('fs').readFileSync(process.env.HOME+'/.fpr/auth.json')).environments.prod.access_token)"

# id_token (user identity in body, prod example)
node -e "console.log(JSON.parse(require('fs').readFileSync(process.env.HOME+'/.fpr/auth.json')).environments.prod.id_token)"
```

## Token Refresh

When `expires_at` < current time but `refresh_token` exists, **auto-refresh using Cognito API** (preferred over OAuth token endpoint):

```python
import json, os, urllib.request, time

AUTH_FILE = os.path.expanduser("~/.fpr/auth.json")
COGNITO_URL = "https://cognito-idp.ap-southeast-1.amazonaws.com/"
CLIENT_IDS = {
    "stg": "38taf824vlbfba3lta3eitcuhi",
    "prod": "i01t804ups4dme8p1kfoat8jb"
}

with open(AUTH_FILE) as f:
    auth = json.load(f)

def refresh_env(env_name):
    env = auth["environments"].get(env_name)
    if not env or not env.get("refresh_token"):
        return False
    if env.get("expires_at", 0) > int(time.time() * 1000):
        return True  # still valid
    body = json.dumps({
        "AuthFlow": "REFRESH_TOKEN_AUTH",
        "ClientId": CLIENT_IDS[env_name],
        "AuthParameters": {"REFRESH_TOKEN": env["refresh_token"]}
    }).encode()
    req = urllib.request.Request(COGNITO_URL, data=body, headers={
        "Content-Type": "application/x-amz-json-1.1",
        "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth"
    })
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        tokens = json.loads(resp.read())["AuthenticationResult"]
        env["id_token"] = tokens["IdToken"]
        env["access_token"] = tokens["AccessToken"]
        env["expires_at"] = int(time.time() * 1000) + (tokens["ExpiresIn"] * 1000)
        with open(AUTH_FILE, "w") as f:
            json.dump(auth, f, indent=2)
        return True
    except Exception:
        return False

# Usage: refresh_env("prod") or refresh_env("stg")
```

**Agent behavior:**
1. Before any MCP call, check `expires_at` for the target environment
2. If expired → run the refresh script above (silent, no user interaction)
3. If refresh fails (refresh_token also expired, ~30 days) → run PKCE login

If refresh fails (400/401) → run PKCE login again.
