# Error Classification

After every `tools/call`, extract the real error before deciding what to do. Check in this order:

1. **`response.error.message`** — gateway-layer error (e.g. `"Unauthorized"`)
2. **`response.result.content[0].text`** (JSON string) — parse, look for `errorMessage`, `message`, `error`, `cause`
3. **`response.result.content[0].text`** (plain text) — Java exception, read class + message
4. **`response.result.content[0].text`** (HTTP passthrough) — e.g. `"HTTP 401: Unauthorized"`
5. **`response._meta.http_status`** — bare HTTP code, no details

Report the extracted error to the user, then follow this recovery table:

| Response | Action | Retry |
|----------|--------|-------|
| HTTP 401 | Re-auth with `python3 ~/.fpr/fpr-auth.py <env>` → retry | 1 |
| JSON-RPC `-32002` + `insufficient_scope` | Force Cognito login with `python3 ~/.fpr/fpr-auth.py login <env>` → retry | 1 |
| HTTP 400 | Re-search schema → correct params → retry | 1 |
| HTTP 429 / 503 | Backoff 1s → 3s → 9s | 3 |
| HTTP 403 / 500 | Report to user | 0 |
| HTTP 200 + `"internal error"` text | Do **not** re-auth or change params; retry same call | 2 |

If 2+ different tools on the same gateway return `"internal error"`, stop. Treat it as a backend outage, report to the user, and do not try variant parameter formats.

Never switch env (prod→stg) to work around errors. Fix the token/params/root cause and retry the same env.

**Non-retryable signals (stop immediately):**
- 404 / "not found" — tool or endpoint doesn't exist
- 403 — permission, not transient
- 500 — report; do not infer auth or parameter variants
- Same error after schema correction (400 case) — not fixable
- Same error after 3 backoff retries (429/503 case) — not transient
