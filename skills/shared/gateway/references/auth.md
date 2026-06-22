# Auth (Local Agent)

> AgentCore agents skip this — runtime handles auth via IAM.

## Reactive flow

Call MCP tools directly. On 401, the agent handles it automatically:

1. `python3 ~/.fpr/fpr-auth.py <env>` — checks token, silent refresh if expired, opens browser if needed
2. `python3 ~/.fpr/fpr-auth.py daemon <env>` — starts background daemon (refreshes token in background, no more 401s going forward)
3. Retry the original MCP call

## Bootstrap

If `~/.fpr/fpr-auth.py` doesn't exist, extract the Python script from the `## Script` section below and write it there. The agent handles this automatically.

## Commands

| Command | Purpose |
|---------|---------|
| `python3 ~/.fpr/fpr-auth.py <env>` | Check / silent refresh / browser login |
| `python3 ~/.fpr/fpr-auth.py daemon <env>` | Start background auto-refresh daemon |
| `python3 ~/.fpr/fpr-auth.py daemon-stop` | Stop the daemon |

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
"""FPR Auth Manager — refresh tokens and start a background daemon."""

import json, os, sys, time, urllib.request, hashlib, base64, http.server
import webbrowser, urllib.parse, secrets, subprocess, signal

AUTH_FILE = os.path.expanduser("~/.fpr/auth.json")
COGNITO_URL = "https://cognito-idp.ap-southeast-1.amazonaws.com/"
CLIENT_IDS = {"stg": "38taf824vlbfba3lta3eitcuhi", "prod": "i01t804ups4dme8p1kfoat8jb"}
PKCE_CONFIG = {
    "stg": {"authorize_url": "https://internal-id.ath.staging-traveloka.com/oauth2/authorize",
            "token_url": "https://internal-id.ath.staging-traveloka.com/oauth2/token"},
    "prod": {"authorize_url": "https://internal-id.ath.traveloka.com/oauth2/authorize",
             "token_url": "https://internal-id.ath.traveloka.com/oauth2/token"},
}
CALLBACK = "http://localhost:18999/callback"
DAEMON_PID = os.path.expanduser("~/.fpr/daemon.pid")
DAEMON_LOG = os.path.expanduser("~/.fpr/daemon.log")

def load():
    return json.load(open(AUTH_FILE)) if os.path.exists(AUTH_FILE) else {"environments": {}}

def save(a):
    os.makedirs(os.path.dirname(AUTH_FILE), exist_ok=True)
    json.dump(a, open(AUTH_FILE, "w"), indent=2)

def valid(env):
    a = load(); e = a.get("environments", {}).get(env, {})
    return e.get("expires_at", 0) > int(time.time() * 1000)

def silent_refresh(env):
    a = load(); e = a.setdefault("environments", {}).setdefault(env, {})
    rt = e.get("refresh_token")
    if not rt: return False
    body = json.dumps({"AuthFlow": "REFRESH_TOKEN_AUTH", "ClientId": CLIENT_IDS[env],
                       "AuthParameters": {"REFRESH_TOKEN": rt}}).encode()
    req = urllib.request.Request(COGNITO_URL, data=body,
        headers={"Content-Type": "application/x-amz-json-1.1",
                 "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth"})
    try:
        t = json.loads(urllib.request.urlopen(req, timeout=10).read())["AuthenticationResult"]
        e["id_token"], e["access_token"] = t["IdToken"], t["AccessToken"]
        e["expires_at"] = int(time.time() * 1000) + (t["ExpiresIn"] * 1000)
        a["active"] = env; save(a); return True
    except Exception as ex:
        print(f"  refresh failed ({ex})", file=sys.stderr); return False

def b64url(b): return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

def pkce_login(env):
    cfg, cid = PKCE_CONFIG[env], CLIENT_IDS[env]
    verifier = secrets.token_urlsafe(64)
    challenge = b64url(hashlib.sha256(verifier.encode()).digest())
    state = secrets.token_urlsafe(16)
    params = urllib.parse.urlencode({
        "response_type": "code", "client_id": cid, "redirect_uri": CALLBACK,
        "scope": "openid email profile", "state": state,
        "code_challenge": challenge, "code_challenge_method": "S256"})
    auth_url = f"{cfg['authorize_url']}?{params}"

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if self.path != "/callback": self.send_error(404); return
            if "error" in q: self.send_error(400); return
            if q.get("state",[""])[0] != state: self.send_error(400); return
            body = urllib.parse.urlencode({
                "grant_type":"authorization_code","client_id":cid,
                "code":q["code"][0],"redirect_uri":CALLBACK,"code_verifier":verifier}).encode()
            req = urllib.request.Request(cfg["token_url"], data=body,
                headers={"Content-Type":"application/x-www-form-urlencoded"})
            try:
                t = json.loads(urllib.request.urlopen(req, timeout=10).read())
            except Exception as ex:
                self.send_error(500, str(ex)); return
            a = load()
            a.setdefault("environments",{})[env] = {
                "id_token":t["id_token"],"access_token":t["access_token"],
                "refresh_token":t.get("refresh_token",""),
                "expires_at":int(time.time()*1000)+(t["expires_in"]*1000)}
            a["active"] = env; save(a)
            self.send_response(200); self.send_header("Content-Type","text/html"); self.end_headers()
            self.wfile.write(b"<h2>Login OK</h2><p>Token saved.</p>")
            print(f"  login OK — {env}")
        def log_message(self,*a): pass

    srv = http.server.HTTPServer(("localhost", 18999), H); srv.timeout = 120
    print(f"  opening browser for {env} login..."); webbrowser.open(auth_url)
    try: srv.handle_request()
    except KeyboardInterrupt: pass
    return valid(env)

def daemon_loop(env):
    os.makedirs(os.path.dirname(DAEMON_LOG), exist_ok=True)
    with open(DAEMON_LOG, "a") as log:
        log.write(f"[{time.ctime()}] daemon started for {env}\n")
    while True:
        try:
            if not valid(env): silent_refresh(env)
        except Exception as ex:
            with open(DAEMON_LOG, "a") as log:
                log.write(f"[{time.ctime()}] error: {ex}\n")
        time.sleep(300)

def start_daemon(env):
    if os.path.exists(DAEMON_PID):
        try:
            os.kill(int(open(DAEMON_PID).read().strip()), 0)
            print("daemon already running"); sys.exit(0)
        except: pass
    p = subprocess.Popen([sys.executable, __file__, "_daemon_loop", env],
        stdout=open(DAEMON_LOG, "a"), stderr=subprocess.STDOUT, start_new_session=True)
    with open(DAEMON_PID, "w") as f: f.write(str(p.pid))
    print(f"daemon started for {env} (PID {p.pid})")

def stop_daemon():
    if not os.path.exists(DAEMON_PID): print("no daemon running"); sys.exit(0)
    pid = int(open(DAEMON_PID).read().strip())
    try: os.kill(pid, signal.SIGTERM)
    except: pass
    os.remove(DAEMON_PID); print(f"daemon stopped")

def main():
    if len(sys.argv) < 2: print(__doc__); sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "daemon-stop": stop_daemon(); return
    env = sys.argv[2] if len(sys.argv) > 2 else ""
    if cmd not in ("_daemon_loop",) and env not in CLIENT_IDS:
        print(f"Unknown env: {env}. Use stg or prod.", file=sys.stderr); sys.exit(1)
    if cmd == "daemon": start_daemon(env)
    elif cmd == "_daemon_loop": daemon_loop(env)
    else:
        if valid(env): print(f"token OK — {env}"); sys.exit(0)
        print(f"refreshing {env}...")
        if silent_refresh(env): print(f"refresh OK — {env}"); sys.exit(0)
        print("refresh failed, opening browser login...")
        if pkce_login(env): print(f"login OK — {env}"); sys.exit(0)
        print("login failed", file=sys.stderr); sys.exit(2)

if __name__ == "__main__": main()
```
