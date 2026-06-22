#!/usr/bin/env python3
"""FPR Auth Manager — login, refresh, and check tokens for fprtool Gateway access.

Usage:
  python3 fpr-auth.py check <env>      Check if token is valid for <env>
  python3 fpr-auth.py refresh <env>    Attempt refresh, fallback to login if needed
  python3 fpr-auth.py login <env>      Force PKCE browser login for <env>
  python3 fpr-auth.py token <env>      Print access_token (for scripts)

Environment: stg | prod
"""

import json, os, sys, time, urllib.request, hashlib, base64, http.server
import webbrowser, urllib.parse, secrets

AUTH_FILE = os.path.expanduser("~/.fpr/auth.json")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

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
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"

# ── helpers ──────────────────────────────────────────

def load_auth():
    if not os.path.exists(AUTH_FILE):
        return {"environments": {}}
    with open(AUTH_FILE) as f:
        return json.load(f)


def save_auth(auth):
    os.makedirs(os.path.dirname(AUTH_FILE), exist_ok=True)
    with open(AUTH_FILE, "w") as f:
        json.dump(auth, f, indent=2)


def is_valid(env_name):
    auth = load_auth()
    env = auth.get("environments", {}).get(env_name, {})
    if not env:
        return False
    return env.get("expires_at", 0) > int(time.time() * 1000)


# ── refresh (Cognito silent) ─────────────────────────

def refresh(env_name):
    """Try Cognito silent refresh. Returns True on success."""
    auth = load_auth()
    env = auth.setdefault("environments", {}).setdefault(env_name, {})
    refresh_token = env.get("refresh_token")
    if not refresh_token:
        return False

    body = json.dumps({
        "AuthFlow": "REFRESH_TOKEN_AUTH",
        "ClientId": CLIENT_IDS[env_name],
        "AuthParameters": {"REFRESH_TOKEN": refresh_token},
    }).encode()
    req = urllib.request.Request(COGNITO_URL, data=body, headers={
        "Content-Type": "application/x-amz-json-1.1",
        "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
    })
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        tokens = json.loads(resp.read())["AuthenticationResult"]
        env["id_token"] = tokens["IdToken"]
        env["access_token"] = tokens["AccessToken"]
        env["expires_at"] = int(time.time() * 1000) + (tokens["ExpiresIn"] * 1000)
        env["obtained_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        auth["active"] = env_name
        save_auth(auth)
        return True
    except Exception as e:
        print(f"  refresh failed ({e})", file=sys.stderr)
        return False


# ── login (PKCE browser flow) ────────────────────────

def b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def login(env_name):
    """PKCE OAuth browser login. Blocks until complete."""
    cfg = PKCE_CONFIG[env_name]
    client_id = CLIENT_IDS[env_name]
    verifier = secrets.token_urlsafe(64)
    challenge = b64url(hashlib.sha256(verifier.encode()).digest())
    state = secrets.token_urlsafe(16)

    params = urllib.parse.urlencode({
        "response_type": "code", "client_id": client_id,
        "redirect_uri": REDIRECT_URI, "scope": "openid email profile",
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
                self.wfile.write(f"Login failed: {q['error'][0]}".encode()); return
            if q.get("state", [""])[0] != state:
                self.send_response(400); self.end_headers()
                self.wfile.write(b"State mismatch"); return
            code = q["code"][0]
            exchange = urllib.parse.urlencode({
                "grant_type": "authorization_code", "client_id": client_id,
                "code": code, "redirect_uri": REDIRECT_URI,
                "code_verifier": verifier,
            }).encode()
            req = urllib.request.Request(cfg["token_url"], data=exchange, headers={
                "Content-Type": "application/x-www-form-urlencoded",
            })
            try:
                resp = urllib.request.urlopen(req, timeout=10)
                tokens = json.loads(resp.read())
            except Exception as e:
                self.send_response(500); self.end_headers()
                self.wfile.write(str(e).encode()); return

            auth = load_auth()
            auth.setdefault("environments", {})[env_name] = {
                "id_token": tokens["id_token"],
                "access_token": tokens["access_token"],
                "refresh_token": tokens.get("refresh_token", ""),
                "expires_at": int(time.time() * 1000) + (tokens["expires_in"] * 1000),
                "obtained_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            auth["active"] = env_name
            save_auth(auth)
            self.send_response(200); self.send_header("Content-Type", "text/html"); self.end_headers()
            self.wfile.write(b"<h2>Login successful!</h2><p>Token saved. You can close this tab.</p>")
            print(f"  login OK — token saved for {env_name}")

        def log_message(self, format, *args):
            pass

    server = http.server.HTTPServer(("localhost", REDIRECT_PORT), Handler)
    server.timeout = 120
    print(f"  opening browser for {env_name} login...")
    webbrowser.open(auth_url)
    try:
        server.handle_request()
    except KeyboardInterrupt:
        pass
    return is_valid(env_name)


# ── main ─────────────────────────────────────────────

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    cmd, env = sys.argv[1], sys.argv[2]
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
        if refresh(env):
            print(f"refresh OK — {env}")
            sys.exit(0)
        print(f"refresh failed, falling back to login...")
        if login(env):
            print(f"login OK — {env}")
            sys.exit(0)
        print("login failed", file=sys.stderr)
        sys.exit(2)

    elif cmd == "login":
        if login(env):
            sys.exit(0)
        sys.exit(1)

    elif cmd == "token":
        auth = load_auth()
        env_data = auth.get("environments", {}).get(env, {})
        if env_data.get("expires_at", 0) > int(time.time() * 1000):
            print(env_data["access_token"])
        else:
            print("EXPIRED", file=sys.stderr)
            sys.exit(1)

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
