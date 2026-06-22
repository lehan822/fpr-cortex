# Auth (Local Agent)

> AgentCore agents skip this — runtime handles auth via IAM.

## Reactive flow

Call MCP tools directly. On 401, the agent handles it automatically:

1. `python3 ~/.fpr/fpr-auth.py <env>` — checks token, silent refresh if expired, opens browser if needed
2. If browser login was triggered → `python3 ~/.fpr/fpr-auth.py daemon <env>` — starts background daemon
3. Daemon keeps token fresh — no more 401s going forward
4. Retry the original MCP call

## Bootstrap

If `~/.fpr/fpr-auth.py` doesn't exist, copy it from this skill's `references/` directory. The agent handles this automatically.

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
