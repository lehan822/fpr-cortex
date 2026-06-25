# Error Classification

After every `tools/call`, extract the real error before deciding what to do. Check in this order:

1. **`response.error.message`** — gateway-layer error (e.g. `"Unauthorized"`)
2. **`response.result.content[0].text`** (JSON string) — parse, look for `errorMessage`, `message`, `error`, `cause`
3. **`response.result.content[0].text`** (plain text) — Java exception, read class + message
4. **`response.result.content[0].text`** (HTTP passthrough) — e.g. `"HTTP 401: Unauthorized"`
5. **`response._meta.http_status`** — bare HTTP code, no details

Report the extracted error to the user, then follow the recovery table in SKILL.md.

**Non-retryable signals (stop immediately):**
- 404 / "not found" — tool or endpoint doesn't exist
- 403 — permission, not transient
- Same error after schema correction (400 case) — not fixable
- Same error after 3 backoff retries (429/503 case) — not transient
