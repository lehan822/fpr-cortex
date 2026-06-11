# FPR Cortex — Onboarding Guide

Get up and running with the FPR AI Agent in **2 minutes**.

## Prerequisites

- [GitHub Copilot CLI](https://docs.github.com/en/copilot/github-copilot-in-the-cli) or [Claude Code](https://claude.ai/code) installed
- Node.js 18+ (for skill installer and PKCE login)
- Traveloka SSO credentials (same as your normal work login)

## Step 1 — Install Skills

```bash
curl -sL https://raw.githubusercontent.com/lehan822/fpr-cortex/main/install.sh | bash
```

This installs all FPR skills (`fpr-shared`, `fpr-pricing`, `fpr-supply`, `fpr-demand`, `fpr-config`) to `~/.agents/skills/`.

## Step 2 — First Query (triggers login)

Open your AI agent (Copilot CLI or Claude Code) and ask:

```
查一下 THB budget balance
```

On first use, the agent will:
1. Detect no auth token exists
2. Open your browser for Traveloka SSO login
3. After login, store tokens at `~/.fpr/auth.json`
4. Execute your query and return results

**That's it! You're ready to use FPR Cortex.**

## What You Can Ask

| Domain | Example Questions |
|--------|------------------|
| Pricing | "THB budget balance", "GA commission rate", "autopilot rules for TH" |
| Supply | "fare adjusters for GA", "provider config for Amadeus" |
| Demand | "search booking ABC123", "fare cache for SIN-BKK" |
| Config | "feature flag X status", "audit log for rule Y" |

## How It Works

```
You (natural language) → AI Agent → Skill (routing) → MCP Gateway → fprtool Backend → Real Data
```

- **Skills** tell the agent which tool to call and how to format parameters
- **MCP Gateway** handles auth, rate limiting, and backend routing
- **fprtool Backend** executes the actual API call and returns data

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Token expired" | Agent auto-refreshes; if it fails, delete `~/.fpr/auth.json` and retry |
| "Operation not found" | Skill may be outdated — re-run the install script |
| "403 Forbidden" | Your SSO account may lack permissions — contact FPR team |
| Slow first response | Normal — first call warms up the Gateway connection |

## Updating Skills

When new operations are added, re-run:

```bash
curl -sL https://raw.githubusercontent.com/lehan822/fpr-cortex/main/install.sh | bash
```

## Architecture (for the curious)

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│  AI Agent   │────▶│  MCP Gateway │────▶│ fprtool Backend │────▶│  Real APIs   │
│ (local CLI) │◀────│  (SG region) │◀────│   (sstg/prod)   │◀────│  (databases) │
└─────────────┘     └──────────────┘     └─────────────────┘     └──────────────┘
       │
       ▼
┌─────────────┐
│   Skills    │  ← routing + domain knowledge (loaded from S3)
│  (S3/local) │
└─────────────┘
```

## Questions?

Reach out to **Le Han** or the FPR Cortex team on Lark.
