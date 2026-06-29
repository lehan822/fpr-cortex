# Auth (Local Agent)

> AgentCore agents skip this — runtime handles auth via IAM.

## Bootstrap (do this first if the script is missing)

`fpr-auth.py` is NOT a separate download — its full source is embedded in the
`## Script` section at the bottom of this file.

- If `~/.fpr/fpr-auth.py` does **not** exist (e.g. you saw
  `No such file or directory`), extract the script from `## Script`, write it
  verbatim to `~/.fpr/fpr-auth.py`, then run `python3 ~/.fpr/fpr-auth.py <env>`
  for first-time token creation. **Do not ask the user to obtain the file — you
  build it.**
- **Auto-update:** the script carries a `SCRIPT_VERSION` constant. If
  `python3 ~/.fpr/fpr-auth.py version` doesn't match the `## Script` version,
  re-extract and overwrite.

## Reactive flow

Call MCP tools directly. Auth recovery is signal-specific:

| Signal | Command | Why |
|--------|---------|-----|
| `401` / expired token | `python3 ~/.fpr/fpr-auth.py <env>` | Auto mode checks validity, silently refreshes when possible, and falls back to browser login only when needed. |
| JSON-RPC `-32002` + `insufficient_scope` | `python3 ~/.fpr/fpr-auth.py login <env>` | Token can be valid but missing scopes; auto/refresh may skip browser login. |
| Need to switch login identity/scopes | `python3 ~/.fpr/fpr-auth.py login <env>` | Force PKCE browser login and save fresh access/id tokens. |

After auth:

1. Run the appropriate command above
2. Retry the original MCP call

`login <env>` binds `localhost:18999/callback`, opens the Cognito authorize URL, exchanges the callback code, and writes `~/.fpr/auth.json`. In Codex sandbox it usually requires escalated execution because localhost binding/browser opening is blocked.

## Commands

| Command | Purpose |
|---------|---------|
| `python3 ~/.fpr/fpr-auth.py <env>` | Auto: check → silent refresh → browser login |
| `python3 ~/.fpr/fpr-auth.py check <env>` | Check if token is still valid |
| `python3 ~/.fpr/fpr-auth.py refresh <env>` | Silent refresh, fallback to login |
| `python3 ~/.fpr/fpr-auth.py login <env>` | Force PKCE browser login |
| `python3 ~/.fpr/fpr-auth.py token <env>` | Print access_token for scripts |
| `python3 ~/.fpr/fpr-auth.py version` | Print SCRIPT_VERSION (for update check) |

## Token model

| Token | Goes into |
|-------|-----------|
| id_token | `context.authServiceToken` |
| access_token | `Authorization: Bearer` |

```bash
# Read both from auth.json (do NOT use fpr-auth.py token — that only prints access_token)
ACCESS_TOKEN=$(python3 -c "import json; print(json.load(open('$HOME/.fpr/auth.json'))['environments']['<env>']['access_token'])")
ID_TOKEN=$(python3 -c "import json; print(json.load(open('$HOME/.fpr/auth.json'))['environments']['<env>']['id_token'])")
```

## Script

The agent writes this to `~/.fpr/fpr-auth.py` on first use:

```python
#!/usr/bin/env python3
"""FPR Auth Manager — login, refresh, and check tokens.

Usage:
  python3 fpr-auth.py <env>          Auto: check → silent refresh → browser login
  python3 fpr-auth.py check <env>    Check if token is valid
  python3 fpr-auth.py refresh <env>  Silent refresh, fallback to login if needed
  python3 fpr-auth.py login <env>    Force PKCE browser login
  python3 fpr-auth.py token <env>    Print access_token (for scripts)

Environment: stg | prod
"""

import json, os, sys, time, urllib.request, hashlib, base64, http.server
import webbrowser, urllib.parse, secrets

SCRIPT_VERSION = 4

AUTH_FILE = os.path.expanduser("~/.fpr/auth.json")
COGNITO_URL = "https://cognito-idp.ap-southeast-1.amazonaws.com/"
CLIENT_IDS = {
    "stg": "38taf824vlbfba3lta3eitcuhi",
    "prod": "i01t804ups4dme8p1kfoat8jb",
}
PKCE_CONFIG = {
    "stg": {
        "authorize_url": "https://internal-id.ath.staging-traveloka.com/oauth2/authorize",
        "token_url": "https://internal-id.ath.staging-traveloka.com/oauth2/token",
    },
    "prod": {
        "authorize_url": "https://internal-id.ath.traveloka.com/oauth2/authorize",
        "token_url": "https://internal-id.ath.traveloka.com/oauth2/token",
    },
}
REDIRECT_PORT = 18999
CALLBACK = f"http://localhost:{REDIRECT_PORT}/callback"

def load_auth():
    if not os.path.exists(AUTH_FILE):
        return {"environments": {}}
    try:
        with open(AUTH_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        print(f"  auth.json corrupt, resetting...", file=sys.stderr)
        os.rename(AUTH_FILE, AUTH_FILE + ".bak")
        return {"environments": {}}

def save_auth(a):
    os.makedirs(os.path.dirname(AUTH_FILE), exist_ok=True)
    with open(AUTH_FILE, "w") as f:
        json.dump(a, f, indent=2)

def is_valid(env_name):
    a = load_auth()
    e = a.get("environments", {}).get(env_name, {})
    return e.get("expires_at", 0) > int(time.time() * 1000)

def silent_refresh(env_name):
    a = load_auth()
    e = a.setdefault("environments", {}).setdefault(env_name, {})
    rt = e.get("refresh_token")
    if not rt:
        print(f"  no refresh token for {env_name}", file=sys.stderr)
        return False
    body = json.dumps({
        "AuthFlow": "REFRESH_TOKEN_AUTH",
        "ClientId": CLIENT_IDS[env_name],
        "AuthParameters": {"REFRESH_TOKEN": rt},
    }).encode()
    req = urllib.request.Request(COGNITO_URL, data=body, headers={
        "Content-Type": "application/x-amz-json-1.1",
        "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
    })
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
        auth_result = resp["AuthenticationResult"]
        e["id_token"] = auth_result["IdToken"]
        e["access_token"] = auth_result["AccessToken"]
        e["expires_at"] = int(time.time() * 1000) + (auth_result["ExpiresIn"] * 1000)
        e["obtained_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        if "RefreshToken" in auth_result:
            e["refresh_token"] = auth_result["RefreshToken"]
        if "Challenges" in resp and resp["Challenges"][0]["ChallengeName"] == "NEW_PASSWORD_REQUIRED":
            print(f"  Cognito requires password change — please use browser login", file=sys.stderr)
            return False
        a["active"] = env_name
        save_auth(a)
        return True
    except Exception as ex:
        print(f"  refresh failed ({ex})", file=sys.stderr)
        return False

def b64url(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

def pkce_login(env_name):
    cfg = PKCE_CONFIG[env_name]
    cid = CLIENT_IDS[env_name]
    verifier = secrets.token_urlsafe(64)
    challenge = b64url(hashlib.sha256(verifier.encode()).digest())
    state = secrets.token_urlsafe(16)

    params = urllib.parse.urlencode({
        "response_type": "code", "client_id": cid,
        "redirect_uri": CALLBACK, "scope": "openid email profile",
        "state": state, "code_challenge": challenge,
        "code_challenge_method": "S256",
    })
    auth_url = f"{cfg['authorize_url']}?{params}"

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            p = urllib.parse.urlparse(self.path)
            q = urllib.parse.parse_qs(p.query)
            if p.path != "/callback":
                self.send_error(404); return
            if "error" in q:
                self.send_response(400); self.end_headers()
                self.wfile.write(f"Login failed: {q['error'][0]}".encode())
                print(f"  login error: {q['error'][0]}", file=sys.stderr); return
            if q.get("state", [""])[0] != state:
                self.send_response(400); self.end_headers()
                self.wfile.write(b"State mismatch"); return
            code = q["code"][0]
            exchange = urllib.parse.urlencode({
                "grant_type": "authorization_code", "client_id": cid,
                "code": code, "redirect_uri": CALLBACK,
                "code_verifier": verifier,
            }).encode()
            req = urllib.request.Request(cfg["token_url"], data=exchange, headers={
                "Content-Type": "application/x-www-form-urlencoded",
            })
            try:
                t = json.loads(urllib.request.urlopen(req, timeout=10).read())
            except Exception as ex:
                self.send_response(500); self.end_headers()
                self.wfile.write(f"Token exchange failed: {ex}".encode())
                print(f"  token exchange failed: {ex}", file=sys.stderr); return

            a = load_auth()
            a.setdefault("environments", {})[env_name] = {
                "id_token": t["id_token"],
                "access_token": t["access_token"],
                "refresh_token": t.get("refresh_token", ""),
                "expires_at": int(time.time() * 1000) + (t["expires_in"] * 1000),
                "obtained_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            a["active"] = env_name
            save_auth(a)
            self.send_response(200); self.send_header("Content-Type", "text/html"); self.end_headers()
            self.wfile.write(b"<h2>Login successful!</h2><p>Token saved. You can close this tab.</p>")
            print(f"  login OK — token saved for {env_name}")

        def log_message(self, format, *args):
            pass

    srv = http.server.HTTPServer(("localhost", REDIRECT_PORT), Handler)
    srv.timeout = 120

    print(f"  opening browser for {env_name} login...")
    opened = webbrowser.open(auth_url)
    if not opened:
        print(f"  browser didn't open automatically — paste this URL:")
        print(f"  {auth_url}")

    try:
        srv.handle_request()
    except KeyboardInterrupt:
        print(f"\n  login cancelled", file=sys.stderr)
        return False
    return is_valid(env_name)

# ── main ─────────────────────────────────────────────

def main():
    args = sys.argv[1:]

    if not args:
        print(__doc__)
        sys.exit(1)

    if len(args) == 1 and args[0] in CLIENT_IDS:
        cmd, env = "auto", args[0]
    elif len(args) >= 2:
        cmd, env = args[0], args[1]
    else:
        cmd = args[0]
        env = args[1] if len(args) > 1 else ""

    if cmd == "version":
        print(SCRIPT_VERSION)
        return

    if env not in CLIENT_IDS:
        print(f"Unknown environment: {env}. Use stg or prod.", file=sys.stderr)
        sys.exit(1)

    if cmd == "check":
        if is_valid(env):
            print(f"OK — {env} token valid")
            sys.exit(0)
        else:
            print(f"EXPIRED — {env} token expired or missing")
            sys.exit(1)

    elif cmd == "refresh":
        if is_valid(env):
            print(f"token still valid for {env}")
            sys.exit(0)
        print(f"refreshing {env}...")
        if silent_refresh(env):
            print(f"refresh OK — {env}")
            sys.exit(0)
        print("refresh failed, opening browser login...")
        if pkce_login(env):
            print(f"login OK — {env}")
            sys.exit(0)
        print("login failed", file=sys.stderr)
        sys.exit(2)

    elif cmd == "login":
        if pkce_login(env):
            print(f"login OK — {env}")
            sys.exit(0)
        print("login failed", file=sys.stderr)
        sys.exit(1)

    elif cmd == "token":
        a = load_auth()
        e = a.get("environments", {}).get(env, {})
        if e.get("expires_at", 0) > int(time.time() * 1000):
            print(e["access_token"])
        else:
            print("EXPIRED", file=sys.stderr)
            sys.exit(1)

    elif cmd == "auto":
        if is_valid(env):
            print(f"token OK — {env}")
            sys.exit(0)
        print(f"refreshing {env}...")
        if silent_refresh(env):
            print(f"refresh OK — {env}")
            sys.exit(0)
        print("refresh failed, opening browser login...")
        if pkce_login(env):
            print(f"login OK — {env}")
            sys.exit(0)
        print("login failed", file=sys.stderr)
        sys.exit(2)

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```
