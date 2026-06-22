# Environment Configuration & Routing

## Default: prod

Unless the user explicitly says "staging" / "stg" / "测试环境", use **prod**.

## Gateway endpoints & prefixes

| Env | Tool Prefix | Gateway Endpoint | Backend | PKCE Client ID (local) |
|-----|-------------|------------------|---------|------------------------|
| stg | `fprtool-fpr` | `https://fpr-cortex-sg-ruypqkcdov.gateway.bedrock-agentcore.ap-southeast-1.amazonaws.com` | `tool-api.fpr.staging-traveloka.com` | `38taf824vlbfba3lta3eitcuhi` |
| prod | `fprtool-prod` | `https://fpr-mcp-gateway-ghntgmtwjb.gateway.bedrock-agentcore.ap-southeast-1.amazonaws.com` | `api-tool.fpr.traveloka.com` | `i01t804ups4dme8p1kfoat8jb` |

> `operation_name` is identical across envs. Only the prefix differs: `{tool_prefix}___{operation_name}`.
> fstg (flight staging, dev) is NOT connected to Gateway — use direct curl for dev testing.

## AgentCore environment resolution

AgentCore agents read the gateway from a deploy-time env var — no login, no token management:

```python
GATEWAY_ENDPOINT = os.environ["GATEWAY_ENDPOINT"]  # stg deploy → stg URL, prod deploy → prod URL
```

## auth.json structure (local)

Single file at `~/.fpr/auth.json` stores tokens for ALL environments:

```json
{
  "active": "prod",
  "environments": {
    "prod": {
      "id_token": "...", "access_token": "...", "refresh_token": "...",
      "expires_at": 1781264126688,
      "gateway": "https://fpr-mcp-gateway-ghntgmtwjb.gateway.bedrock-agentcore.ap-southeast-1.amazonaws.com",
      "tool_prefix": "fprtool-prod"
    },
    "stg": {
      "id_token": "...", "access_token": "...", "refresh_token": "...",
      "expires_at": 1781255897391,
      "gateway": "https://fpr-cortex-sg-ruypqkcdov.gateway.bedrock-agentcore.ap-southeast-1.amazonaws.com",
      "tool_prefix": "fprtool-fpr"
    }
  }
}
```

Do not parse this manually — `fpr-auth.py` handles env switching. See [`auth.md`](auth.md).
