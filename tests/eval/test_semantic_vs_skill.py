#!/usr/bin/env python3
"""Compare: Skill-only (no semantic search) vs Skill+SemanticSearch (current mode).

Mode A (skill-only): Skill routing guide + skill tool names → LLM picks tool
Mode B (skill+search): Skill routing guide + semantic search results → LLM picks tool

Usage:
  python tests/eval/test_semantic_vs_skill.py --env stg [--limit 10]
"""
import json, os, sys, time, subprocess, argparse, re
from pathlib import Path

AUTH_FILE = os.path.expanduser("~/.fpr/auth.json")
SKILLS_DIR = Path("skills/domain")
AWS_PROFILE = "Engineer@tvlk-fpr-stg"
AWS_REGION = "ap-southeast-1"
BEDROCK_MODEL = "anthropic.claude-3-haiku-20240307-v1:0"


def load_auth(env="stg"):
    with open(AUTH_FILE) as f:
        auth = json.load(f)
    envs = auth.get("environments", {})
    e = envs.get(env, auth)
    if e.get("expires_at", 0) < time.time() * 1000:
        print(f"❌ Token expired for {env}. Run PKCE login first.")
        sys.exit(1)
    return e["access_token"], e["id_token"], e["gateway"], e.get("tool_prefix", "fprtool-fpr")


def mcp_call(gateway, access_token, method, params=None):
    body = {"jsonrpc": "2.0", "id": "1", "method": method}
    if params:
        body["params"] = params
    result = subprocess.run(
        ["curl", "-sf", "-X", "POST", f"{gateway}/mcp",
         "-H", f"Authorization: Bearer {access_token}",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(body)],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except:
        return None


def semantic_search(gateway, access_token, query):
    """Call x_amz_bedrock_agentcore_search → returns tools with schema."""
    resp = mcp_call(gateway, access_token, "tools/call", {
        "name": "x_amz_bedrock_agentcore_search",
        "arguments": {"query": query}
    })
    if not resp:
        return []
    content = resp.get("result", {}).get("content", [])
    if content and content[0].get("type") == "text":
        try:
            data = json.loads(content[0]["text"])
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "tools" in data:
                return data["tools"]
            return [data]
        except:
            return []
    return []


def llm_route(prompt, system_prompt):
    """Call Bedrock Claude to route tool selection."""
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "messages": [{"role": "user", "content": prompt}],
        "system": system_prompt,
        "max_tokens": 100,
        "temperature": 0
    }
    body_file = "/tmp/bedrock-eval-body.json"
    out_file = "/tmp/bedrock-eval-out.json"
    with open(body_file, "w") as f:
        json.dump(body, f)

    result = subprocess.run(
        ["aws", "bedrock-runtime", "invoke-model",
         "--model-id", BEDROCK_MODEL,
         "--region", AWS_REGION,
         "--content-type", "application/json",
         "--accept", "application/json",
         "--body", f"fileb://{body_file}",
         "--profile", AWS_PROFILE,
         out_file],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        return f"ERROR: {result.stderr[:100]}"
    try:
        with open(out_file) as f:
            resp = json.load(f)
        return resp["content"][0]["text"].strip()
    except Exception as e:
        return f"ERROR: {e}"


def load_all_skills():
    """Load all domain skills with routing guides and tool lists."""
    skills = {}
    for skill_file in SKILLS_DIR.rglob("SKILL.md"):
        with open(skill_file) as f:
            content = f.read()
        name_match = re.search(r'^name:\s*(.+)$', content, re.MULTILINE)
        desc_match = re.search(r'^description:\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
        tools_match = re.search(r'^tools:\s*\n((?:\s+-\s+.+\n)+)', content, re.MULTILINE)

        if not name_match:
            continue
        name = name_match.group(1).strip()
        tools = []
        if tools_match:
            tools = re.findall(r'^\s+-\s+(\S+)', tools_match.group(1), re.MULTILINE)

        routing = ""
        routing_match = re.search(r'## Routing Guide\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
        if routing_match:
            routing = routing_match.group(1).strip()

        skills[name] = {
            "description": desc_match.group(1).strip() if desc_match else "",
            "tools": tools,
            "routing_guide": routing,
        }
    return skills


def build_skill_context(skills):
    """Build skill descriptions + routing guides for system prompt."""
    parts = []
    for name, info in skills.items():
        parts.append(f"### {name}\n{info['description']}")
        if info['routing_guide']:
            parts.append(f"Routing:\n{info['routing_guide']}")
        parts.append("")
    return "\n".join(parts)


def build_system_prompt_a(skill_context, skills):
    """Mode A: skill routing + skill tool names only."""
    tool_lines = []
    for name, info in skills.items():
        for tool in info['tools']:
            tool_lines.append(f"- {tool}")
    tool_list = "\n".join(tool_lines)

    return f"""You are an FPR tool router. Given a user query about flight pricing/revenue,
select the SINGLE best tool to call.

Reply with ONLY the operation name (e.g., load_autopilot_rules). Nothing else.
If no tool matches, reply "NONE".

## Skills & Routing:
{skill_context}

## All Available Tools:
{tool_list}"""


def build_system_prompt_b(skill_context, search_results, tool_prefix):
    """Mode B: skill routing + semantic search results."""
    tool_lines = []
    for tool in search_results:
        if isinstance(tool, dict):
            tname = tool.get("name", "").replace(f"{tool_prefix}___", "")
            desc = tool.get("description", "")[:150]
            tool_lines.append(f"- {tname}: {desc}")
    tool_list = "\n".join(tool_lines) if tool_lines else "(no search results)"

    return f"""You are an FPR tool router. Given a user query about flight pricing/revenue,
select the SINGLE best tool to call from the search results below.

Reply with ONLY the operation name (e.g., load_autopilot_rules). Nothing else.
If no tool matches, reply "NONE".

## Skills & Routing:
{skill_context}

## Semantic Search Results (most relevant tools):
{tool_list}"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", default="stg", choices=["stg", "prod"])
    parser.add_argument("--cases", default="/tmp/eval-75-cases.json")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    access_token, id_token, gateway, tool_prefix = load_auth(args.env)

    with open(args.cases) as f:
        cases = json.load(f)
    if args.limit:
        cases = cases[:args.limit]

    skills = load_all_skills()
    skill_context = build_skill_context(skills)
    total_tools = sum(len(s['tools']) for s in skills.values())

    print(f"✅ Auth ({args.env}), Gateway: {gateway[:50]}...")
    print(f"✅ LLM: Bedrock {BEDROCK_MODEL}")
    print(f"✅ Skills: {len(skills)} domains, {total_tools} tools")
    print(f"✅ Cases: {len(cases)}")
    print(f"\n{'='*80}")
    print(f"{'ID':<8} {'Mode A (Skill only)':<35} {'Mode B (+Search)':<35} {'Eq':>3} {'#B'}")
    print(f"{'='*80}")

    results = []
    match_count = 0

    for i, case in enumerate(cases):
        prompt = case["prompt"]
        case_id = case["id"]

        # Mode A: Skill only
        sys_a = build_system_prompt_a(skill_context, skills)
        selected_a = llm_route(prompt, sys_a)

        # Mode B: Skill + Semantic Search
        search_results = semantic_search(gateway, access_token, prompt)
        sys_b = build_system_prompt_b(skill_context, search_results, tool_prefix)
        selected_b = llm_route(prompt, sys_b)

        same = selected_a.strip() == selected_b.strip()
        if same:
            match_count += 1
        eq_mark = "✅" if same else "❌"

        # Clean display
        disp_a = selected_a[:33] if not selected_a.startswith("ERROR") else "ERROR"
        disp_b = selected_b[:33] if not selected_b.startswith("ERROR") else "ERROR"

        print(f"{case_id:<8} {disp_a:<35} {disp_b:<35} {eq_mark:>3} {len(search_results):>2}")

        results.append({
            "id": case_id,
            "category": case["category"],
            "prompt": prompt,
            "mode_a": selected_a.strip(),
            "mode_b": selected_b.strip(),
            "search_count": len(search_results),
            "same": same
        })

        time.sleep(0.2)

    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY — {BEDROCK_MODEL}")
    print(f"{'='*80}")
    print(f"Total:         {len(cases)}")
    print(f"Same result:   {match_count}/{len(cases)} ({match_count/len(cases)*100:.1f}%)")
    print(f"Different:     {len(cases)-match_count}/{len(cases)} ({(len(cases)-match_count)/len(cases)*100:.1f}%)")

    avg_search = sum(r["search_count"] for r in results) / len(results)
    print(f"Avg search #:  {avg_search:.1f} tools returned")
    print(f"Context size:  Mode A={total_tools} tools | Mode B=~{avg_search:.0f} tools")

    # Breakdown
    for cat in ["TS", "PA", "ER"]:
        cat_r = [r for r in results if r["category"] == cat]
        if cat_r:
            cat_same = sum(1 for r in cat_r if r["same"])
            print(f"  {cat}: {cat_same}/{len(cat_r)} same ({cat_same/len(cat_r)*100:.0f}%)")

    # Show differences
    diffs = [r for r in results if not r["same"]]
    if diffs:
        print(f"\n--- Differences ({len(diffs)}) ---")
        for d in diffs:
            print(f"  {d['id']}: A={d['mode_a'][:30]} | B={d['mode_b'][:30]}")
            print(f"       Q: {d['prompt'][:60]}")

    # Save
    output = {
        "env": args.env, "model": BEDROCK_MODEL,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(cases), "same": match_count,
        "same_pct": round(match_count / len(cases) * 100, 1),
        "avg_search_count": round(avg_search, 1),
        "skill_tools": total_tools,
        "cases": results
    }
    with open("tests/eval/results-semantic-vs-skill.json", "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Saved to tests/eval/results-semantic-vs-skill.json")


if __name__ == "__main__":
    main()
