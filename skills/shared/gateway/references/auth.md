# Auth (Local Agent)

> AgentCore agents skip this entirely — runtime handles Gateway auth via IAM/SigV4.
> This file is for Local agents (Copilot CLI / Cursor / Claude Code) only.

## The one rule

Before **any** MCP call, run:

```bash
python3 ~/.fpr/fpr-auth.py <env>
```

Proceed only on exit code 0. This single command handles: valid token → silent refresh → browser login fallback.

- **Do NOT** probe the gateway first and check auth after a 401.
- **Do NOT** read `auth.json` manually.
- **Do NOT** ask the user about auth — resolve silently.

## One-time bootstrap

If `~/.fpr/fpr-auth.py` doesn't exist yet, copy it from this skill's `references/` directory. The agent handles this automatically — no manual steps needed.

## Script commands

| Command | Purpose |
|---------|---------|
| `python3 ~/.fpr/fpr-auth.py <env>` | Refresh + fallback to login if needed (**use this**) |
| `python3 ~/.fpr/fpr-auth.py daemon <env>` | Start background auto-refresh daemon |
| `python3 ~/.fpr/fpr-auth.py daemon-stop` | Stop the daemon |

Internally the default command does: valid → exit 0 / expired → Cognito silent refresh → exit 0 / refresh fails → browser PKCE login → exit 0 / all fail → exit 2.

## Token model

**Local agent** uses two tokens, both owned by the user, both in `~/.fpr/auth.json`:

| Token | Goes into |
|-------|-----------|
| User id_token | request body `context.authServiceToken` |
| access_token | `Authorization: Bearer` header |

**AgentCore agent** (for reference): user id_token passed in from caller → `context.authServiceToken`; M2M token auto-managed by runtime IAM role (never ask user for client_id/secret).

PKCE login is handled automatically by `fpr-auth.py` — run it, it opens the browser when needed.
