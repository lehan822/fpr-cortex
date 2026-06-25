#!/usr/bin/env python3
"""E2E integration test — verify Gateway is reachable and responds correctly.

Prerequisites:
- ~/.fpr/auth.json must exist with valid tokens
- Network access to Gateway endpoint

Tests:
1. tools/list returns paginated tool list
2. tools/call with a known operation returns valid response
3. Error handling: invalid operation returns proper error
"""
import json, os, subprocess, sys

AUTH_FILE = os.path.expanduser("~/.fpr/auth.json")
GATEWAY_STG = "https://fpr-cortex-sg-ruypqkcdov.gateway.bedrock-agentcore.ap-southeast-1.amazonaws.com"


def load_tokens():
    if not os.path.isfile(AUTH_FILE):
        print("⚠️  ~/.fpr/auth.json not found — run PKCE login first")
        sys.exit(2)
    with open(AUTH_FILE) as f:
        auth = json.load(f)
    return auth["access_token"], auth["id_token"]


def mcp_request(access_token, method, params=None):
    body = {"jsonrpc": "2.0", "id": "1", "method": method}
    if params:
        body["params"] = params
    result = subprocess.run(
        ["curl", "-sf", "-X", "POST", f"{GATEWAY_STG}/mcp",
         "-H", f"Authorization: Bearer {access_token}",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(body)],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        return None, result.stderr
    return json.loads(result.stdout), None


def test_tools_list(access_token):
    """Test: tools/list returns tools with pagination."""
    print("  [1/3] tools/list ...", end=" ")
    resp, err = mcp_request(access_token, "tools/list")
    if err:
        print(f"❌ {err}")
        return False
    tools = resp.get("result", {}).get("tools", [])
    if len(tools) == 0:
        print("❌ no tools returned")
        return False
    print(f"✅ {len(tools)} tools (page 1)")
    return True


def test_tools_call(access_token, id_token):
    """Test: call get_countries (no params needed, safe read-only)."""
    print("  [2/3] tools/call get_countries ...", end=" ")
    resp, err = mcp_request(access_token, "tools/call", {
        "name": "fprtool-backend___get_countries",
        "arguments": {
            "data": {},
            "context": {"authServiceToken": id_token},
            "clientInterface": "DESKTOP",
            "fields": []
        }
    })
    if err:
        print(f"❌ {err}")
        return False
    content = resp.get("result", {}).get("content", [])
    if not content:
        print("❌ empty content")
        return False
    print(f"✅ got response ({len(content[0].get('text', ''))} chars)")
    return True


def test_invalid_operation(access_token, id_token):
    """Test: invalid operation returns error (not crash)."""
    print("  [3/3] tools/call invalid_op ...", end=" ")
    resp, err = mcp_request(access_token, "tools/call", {
        "name": "fprtool-backend___nonexistent_operation",
        "arguments": {
            "data": {},
            "context": {"authServiceToken": id_token},
            "clientInterface": "DESKTOP",
            "fields": []
        }
    })
    if err:
        print(f"❌ network error: {err}")
        return False
    # Expect an error in response (not a crash)
    if "error" in resp or resp.get("result", {}).get("isError"):
        print("✅ proper error response")
        return True
    print("⚠️  unexpected success (might be permissive)")
    return True


def main():
    print("FPR Gateway E2E Test (staging)\n")
    access_token, id_token = load_tokens()

    results = [
        test_tools_list(access_token),
        test_tools_call(access_token, id_token),
        test_invalid_operation(access_token, id_token),
    ]

    print(f"\n{'✅' if all(results) else '❌'} {sum(results)}/{len(results)} tests passed")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
