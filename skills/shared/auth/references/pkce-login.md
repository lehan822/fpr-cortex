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

## Reading Tokens

```bash
# Check whether expired
node -e "const a=JSON.parse(require('fs').readFileSync(process.env.HOME+'/.fpr/auth.json'));
  if(a.expires_at<Date.now()){console.log('EXPIRED');process.exit(1);}
  console.log('OK');"

# access_token (Gateway auth header)
node -e "console.log(JSON.parse(require('fs').readFileSync(process.env.HOME+'/.fpr/auth.json')).access_token)"

# id_token (user identity in body)
node -e "console.log(JSON.parse(require('fs').readFileSync(process.env.HOME+'/.fpr/auth.json')).id_token)"
```

## Token Refresh

When `expires_at` < current time but `refresh_token` exists, try refreshing first:

```bash
ENV=$(cat ~/.fpr/auth.json | node -e "process.stdin.on('data',d=>console.log(JSON.parse(d).env||'stg'))")
REFRESH_TOKEN=$(cat ~/.fpr/auth.json | node -e "process.stdin.on('data',d=>console.log(JSON.parse(d).refresh_token))")

# stg: TOKEN_URL=https://internal-id.ath.staging-traveloka.com/oauth2/token CLIENT_ID=38taf824vlbfba3lta3eitcuhi
# prod: TOKEN_URL=https://internal-id.ath.traveloka.com/oauth2/token CLIENT_ID=i01t804ups4dme8p1kfoat8jb

curl -s -X POST "$TOKEN_URL" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=refresh_token&client_id=$CLIENT_ID&refresh_token=$REFRESH_TOKEN"
```

If refresh succeeds → update `~/.fpr/auth.json`.
If refresh fails (400/401) → run PKCE login again.
