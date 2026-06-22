#!/usr/bin/env python3
"""FPR Auth Manager — refresh tokens and start a background daemon.

  python3 fpr-auth.py <env>          Refresh token (silent if possible, browser login as fallback)
  python3 fpr-auth.py daemon <env>   Start background auto-refresh daemon
  python3 fpr-auth.py daemon-stop    Stop the daemon

Environment: stg | prod
"""

import json, os, sys, time, urllib.request, hashlib, base64, http.server
import webbrowser, urllib.parse, secrets, subprocess, signal

AUTH_FILE = os.path.expanduser("~/.fpr/auth.json")

COGNITO_URL = "https://cognito-idp.ap-southeast-1.amazonaws.com/"
CLIENT_IDS = {"stg": "38taf824vlbfba3lta3eitcuhi", "prod": "i01t804ups4dme8p1kfoat8jb"}
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
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"
DAEMON_PID = os.path.expanduser("~/.fpr/daemon.pid")
DAEMON_LOG = os.path.expanduser("~/.fpr/daemon.log")
REFRESH_BEFORE_SEC = 600   # refresh if expires within 10 min
CHECK_INTERVAL_SEC = 300   # check every 5 min

def load():
    return json.load(open(AUTH_FILE)) if os.path.exists(AUTH_FILE) else {"environments": {}}

def save(auth):
    os.makedirs(os.path.dirname(AUTH_FILE), exist_ok=True)
    json.dump(auth, open(AUTH_FILE, "w"), indent=2)

def valid(env):
    a = load()
    e = a.get("environments", {}).get(env, {})
    return e.get("expires_at", 0) > int(time.time() * 1000)


def silent_refresh(env):
    """Cognito silent refresh. Returns True on success."""
    a = load()
    e = a.setdefault("environments", {}).setdefault(env, {})
    rt = e.get("refresh_token")
    if not rt:
        return False
    body = json.dumps({"AuthFlow": "REFRESH_TOKEN_AUTH", "ClientId": CLIENT_IDS[env],
                       "AuthParameters": {"REFRESH_TOKEN": rt}}).encode()
    req = urllib.request.Request(COGNITO_URL, data=body, headers={
        "Content-Type": "application/x-amz-json-1.1",
        "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
    })
    try:
        t = json.loads(urllib.request.urlopen(req, timeout=10).read())["AuthenticationResult"]
        e["id_token"] = t["IdToken"]
        e["access_token"] = t["AccessToken"]
        e["expires_at"] = int(time.time() * 1000) + (t["ExpiresIn"] * 1000)
        a["active"] = env
        save(a)
        return True
    except Exception as ex:
        print(f"  refresh failed ({ex})", file=sys.stderr)
        return False


def b64url(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def pkce_login(env):
    """PKCE browser login. Blocks until complete."""
    cfg = PKCE_CONFIG[env]
    cid = CLIENT_IDS[env]
    verifier = secrets.token_urlsafe(64)
    challenge = b64url(hashlib.sha256(verifier.encode()).digest())
    state = secrets.token_urlsafe(16)
    params = urllib.parse.urlencode({
        "response_type": "code", "client_id": cid,
        "redirect_uri": REDIRECT_URI, "scope": "openid email profile",
        "state": state, "code_challenge": challenge, "code_challenge_method": "S256",
    })
    auth_url = f"{cfg['authorize_url']}?{params}"

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if self.path != "/callback": self.send_error(404); return
            if "error" in q: self.send_error(400, f"Login failed: {q['error'][0]}"); return
            if q.get("state", [""])[0] != state: self.send_error(400, "State mismatch"); return
            code = q["code"][0]
            body = urllib.parse.urlencode({
                "grant_type": "authorization_code", "client_id": cid,
                "code": code, "redirect_uri": REDIRECT_URI, "code_verifier": verifier,
            }).encode()
            req = urllib.request.Request(cfg["token_url"], data=body,
                headers={"Content-Type": "application/x-www-form-urlencoded"})
            try:
                t = json.loads(urllib.request.urlopen(req, timeout=10).read())
            except Exception as ex:
                self.send_error(500, str(ex)); return
            a = load()
            a.setdefault("environments", {})[env] = {
                "id_token": t["id_token"], "access_token": t["access_token"],
                "refresh_token": t.get("refresh_token", ""),
                "expires_at": int(time.time() * 1000) + (t["expires_in"] * 1000),
            }
            a["active"] = env
            save(a)
            self.send_response(200); self.send_header("Content-Type", "text/html"); self.end_headers()
            self.wfile.write(b"<h2>Login OK</h2><p>Token saved. Close this tab.</p>")
            print(f"  login OK — {env}")

        def log_message(self, *a): pass

    srv = http.server.HTTPServer(("localhost", REDIRECT_PORT), H)
    srv.timeout = 120
    print(f"  opening browser for {env} login...")
    webbrowser.open(auth_url)
    try:
        srv.handle_request()
    except KeyboardInterrupt:
        pass
    return valid(env)


def daemon_loop(env):
    os.makedirs(os.path.dirname(DAEMON_LOG), exist_ok=True)
    with open(DAEMON_LOG, "a") as log:
        log.write(f"[{time.ctime()}] daemon started for {env}\n")
    while True:
        try:
            if not valid(env):
                with open(DAEMON_LOG, "a") as log:
                    log.write(f"[{time.ctime()}] token expiring, refreshing...\n")
                silent_refresh(env)
        except Exception as ex:
            with open(DAEMON_LOG, "a") as log:
                log.write(f"[{time.ctime()}] error: {ex}\n")
        time.sleep(CHECK_INTERVAL_SEC)


def start_daemon(env):
    if os.path.exists(DAEMON_PID):
        try:
            os.kill(int(open(DAEMON_PID).read().strip()), 0)
            print("daemon already running"); sys.exit(0)
        except (ProcessLookupError, ValueError, FileNotFoundError):
            pass
    p = subprocess.Popen([sys.executable, __file__, "_daemon_loop", env],
        stdout=open(DAEMON_LOG, "a"), stderr=subprocess.STDOUT, start_new_session=True)
    with open(DAEMON_PID, "w") as f:
        f.write(str(p.pid))
    print(f"daemon started for {env} (PID {p.pid})")


def stop_daemon():
    if not os.path.exists(DAEMON_PID):
        print("no daemon running"); sys.exit(0)
    pid = int(open(DAEMON_PID).read().strip())
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"daemon stopped (PID {pid})")
    except ProcessLookupError:
        pass
    os.remove(DAEMON_PID)


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "daemon-stop":
        stop_daemon(); return

    env = sys.argv[2] if len(sys.argv) > 2 else ""
    if cmd not in ("_daemon_loop",) and env not in CLIENT_IDS:
        print(f"Unknown env: {env}. Use stg or prod.", file=sys.stderr); sys.exit(1)

    if cmd == "daemon":
        start_daemon(env)
    elif cmd == "_daemon_loop":
        daemon_loop(env)
    else:
        # default: refresh (check → silent refresh → PKCE login fallback)
        if valid(env):
            print(f"token OK — {env}"); sys.exit(0)
        print(f"refreshing {env}...")
        if silent_refresh(env):
            print(f"refresh OK — {env}"); sys.exit(0)
        print("refresh failed, opening browser login...")
        if pkce_login(env):
            print(f"login OK — {env}"); sys.exit(0)
        print("login failed", file=sys.stderr); sys.exit(2)


if __name__ == "__main__":
    main()
