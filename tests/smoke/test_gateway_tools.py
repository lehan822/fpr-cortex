#!/usr/bin/env python3
"""
Smoke test: verify all skill-declared tools exist on Gateway and are callable.

Usage:
  python tests/smoke/test_gateway_tools.py [--env stg|prod]
  python tests/smoke/test_gateway_tools.py --skip-search --skip-call  # fast coverage-only

Checks:
  1. All tools in skills/ exist on Gateway (tools/list)
  2. Each tool is callable (tools/call returns valid JSON-RPC, not "unknown tool")
  3. Search can find each tool by name (schema loader test)

Does NOT test business logic — only connectivity and registration.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR = ROOT / "skills" / "domain"
AUTH_FILE = Path.home() / ".fpr" / "auth.json"


def load_skill_tools():
    tools = {}
    for f in SKILLS_DIR.rglob("SKILL.md"):
        domain = f.parent.name
        content = f.read_text()
        m = re.search(r"^tools:\s*\n((?:\s+-\s+.+\n)+)", content, re.MULTILINE)
        if m:
            for t in re.findall(r"^\s+-\s+(\S+)", m.group(1), re.MULTILINE):
                tools[t] = domain
    return tools


def load_auth(env_name):
    with open(AUTH_FILE) as f:
        auth = json.load(f)
    env = auth["environments"][env_name]
    return env["gateway"], env["access_token"], env["id_token"], env.get("tool_prefix", "fprtool-fpr")


def mcp_call(gateway, token, method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": "1", "method": method, "params": params})
    r = subprocess.run(
        ["curl", "-sf", "--max-time", "15", "-X", "POST", f"{gateway}/mcp",
         "-H", f"Authorization: Bearer {token}", "-H", "Content-Type: application/json",
         "-d", body],
        capture_output=True, text=True
    )
    if r.returncode != 0 or not r.stdout:
        return None
    return json.loads(r.stdout)


def get_gateway_tools(gateway, token, prefix):
    all_tools = {}
    cursor = None
    for _ in range(5):
        params = {"cursor": cursor} if cursor else {}
        resp = mcp_call(gateway, token, "tools/list", params)
        if not resp or "result" not in resp:
            break
        for t in resp["result"]["tools"]:
            name = t["name"].replace(f"{prefix}___", "")
            if not name.startswith("x_amz"):
                all_tools[name] = t
        cursor = resp["result"].get("nextCursor")
        if not cursor:
            break
    return all_tools


def test_search_finds_tool(gateway, token, tool_name):
    resp = mcp_call(gateway, token, "tools/call", {
        "name": "x_amz_bedrock_agentcore_search",
        "arguments": {"query": tool_name}
    })
    if not resp or "result" not in resp:
        return False, "no response"
    content = resp["result"].get("content", [])
    if not content:
        return False, "empty content"
    data = json.loads(content[0]["text"])
    tools = data.get("tools", [])
    prefix = "fprtool-fpr___"
    found_names = [t["name"].replace(prefix, "") for t in tools[:3]]
    if tool_name in found_names:
        return True, f"pos #{found_names.index(tool_name) + 1}"
    return False, f"not in top3, got: {found_names[:3]}"


def test_tool_callable(gateway, token, prefix, id_token, tool_name):
    resp = mcp_call(gateway, token, "tools/call", {
        "name": f"{prefix}___{tool_name}",
        "arguments": {
            "data": {},
            "context": {"authServiceToken": id_token},
            "clientInterface": "DESKTOP",
            "fields": []
        }
    })
    if not resp:
        return False, "no response"
    if "error" in resp:
        msg = resp["error"].get("message", "")
        if "Unknown tool" in msg:
            return False, "unknown tool"
        return False, f"error: {msg[:60]}"
    content = resp.get("result", {}).get("content", [])
    if content:
        txt = content[0].get("text", "")
        if "Exception" in txt or "error" in txt[:20].lower():
            return True, "reachable (backend error with empty params)"
        return True, "success"
    return True, "reachable"


def main():
    parser = argparse.ArgumentParser(description="Smoke test Gateway tools")
    parser.add_argument("--env", default="stg", choices=["stg", "prod"])
    parser.add_argument("--skip-search", action="store_true")
    parser.add_argument("--skip-call", action="store_true")
    args = parser.parse_args()

    skill_tools = load_skill_tools()
    gateway, token, id_token, prefix = load_auth(args.env)
    gateway_tools = get_gateway_tools(gateway, token, prefix)

    print(f"Env: {args.env} | Skills: {len(skill_tools)} tools | Gateway: {len(gateway_tools)} tools\n")

    passed = failed = warnings = 0

    # Test 1: Coverage
    print("── TEST 1: Skill → Gateway coverage ──")
    for tool in sorted(skill_tools.keys()):
        if tool in gateway_tools:
            passed += 1
        else:
            print(f"  ❌ {tool} (domain: {skill_tools[tool]}) — not on Gateway")
            failed += 1

    orphans = set(gateway_tools.keys()) - set(skill_tools.keys())
    if orphans:
        for t in sorted(orphans):
            print(f"  ⚠️  {t} — on Gateway but not in any skill")
            warnings += 1

    print(f"  {passed} exist, {failed} missing, {warnings} orphans\n")

    # Test 2: Callable
    if not args.skip_call:
        print("── TEST 2: Tools callable ──")
        call_pass = call_fail = 0
        for tool in sorted(skill_tools.keys()):
            if tool not in gateway_tools:
                continue
            ok, msg = test_tool_callable(gateway, token, prefix, id_token, tool)
            if ok:
                call_pass += 1
            else:
                print(f"  ❌ {tool} — {msg}")
                call_fail += 1
            time.sleep(0.2)
        passed += call_pass
        failed += call_fail
        print(f"  {call_pass} callable, {call_fail} failed\n")

    # Test 3: Search
    if not args.skip_search:
        print("── TEST 3: Search finds tool (schema loader) ──")
        search_pass = search_warn = 0
        for tool in sorted(skill_tools.keys()):
            if tool not in gateway_tools:
                continue
            ok, msg = test_search_finds_tool(gateway, token, tool)
            if ok:
                search_pass += 1
            else:
                print(f"  ⚠️  {tool} — {msg}")
                search_warn += 1
            time.sleep(0.3)
        passed += search_pass
        warnings += search_warn
        print(f"  {search_pass} found, {search_warn} missed\n")

    # Summary
    print(f"{'=' * 50}")
    print(f"TOTAL: {passed} passed | {failed} failed | {warnings} warnings")
    print(f"{'=' * 50}")
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
