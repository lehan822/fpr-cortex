# Error Classification & Auto-Recovery

## Error Detection — MANDATORY after every MCP call

After EVERY `tools/call`, check the response before considering it successful. Do NOT just report "call failed" or pass through a bare HTTP code. Read the response and extract the actual error.

### Where to look (in order):

**1. Gateway-layer error** — `response.error` field exists:
```json
{"error": {"code": -32000, "message": "Unauthorized"}}
```
→ The `message` field IS the error. Read it.

**2. Backend error nested in result content** — `response.result.content[0].text` is a JSON string:
```json
{"result": {"content": [{"type": "text", "text": "{\"errorMessage\": \"Missing required field\", \"cause\": \"...\"}"}]}}
```
→ Parse the `text` as JSON. Look for keys: `errorMessage`, `message`, `error`, `cause`. These are the actual error.

**3. Java exception in result content** — `response.result.content[0].text` is plain text:
```
java.lang.ArrayIndexOutOfBoundsException: Index 2 out of bounds for length 2
    at com.traveloka.fpr.controller.AutoPilotController.loadRules(AutoPilotController.java:45)
```
→ Read the exception class and message. Usually means: wrong number of parameters or missing required field.

**4. HTTP passthrough in result content** — `response.result.content[0].text` is:
```
HTTP 401: Unauthorized
```
→ Read the status code + message.

**5. Bare HTTP status** — only `response._meta.http_status` is set:
```json
{"_meta": {"http_status": 500, "body": "<html>...</html>"}}
```
→ Read the HTTP code. If no body details, report: "Backend returned HTTP 500 (no details). Check Datadog."

### What to do after extraction

Print the error to the user in this format:
```
❌ load_autopilot_rules failed: ArrayIndexOutOfBoundsException
   This means a required parameter is missing. Re-searching Gateway schema...
```

Then follow the recovery table below.

## Error Patterns & Recovery

### 401 — Authentication Expired

**Detection:** `response.error.message` contains "not authorized" / "Unauthorized" / "ExpiredToken"
**OR** `response.result.content[0].text` parses as JSON with `error` field containing "auth" / "token" / "session"

**Recovery:**
```
python3 ~/.fpr/fpr-auth.py refresh <env>    # silent Cognito refresh
→ success → retry original MCP call
→ failure → python3 ~/.fpr/fpr-auth.py login <env>   # PKCE browser login
           → retry original MCP call
```

### 400 — Parameter Validation Error

**Detection:** statusCode=400 OR error message contains:
- "ArrayIndexOutOfBoundsException" — 5 required fields missing (autopilot)
- "validation" — field name or value mismatch
- "missing.*parameter" — missing required field
- "invalid.*value" — wrong enum or format

**Recovery:**
1. Extract the operation name from the failed request
2. `x_amz_bedrock_agentcore_search(operationName)` → get actual inputSchema
3. Compare Skill-documented params with Schema params
4. If mismatch: rebuild request using Schema field names → retry
5. If match: report specific error to user (no auto-fix)

### 429 / 503 — Transient Error

**Detection:** statusCode=429 ("Too Many Requests") or 503 ("Service Unavailable")

**Recovery:**
```
Retry 1: wait 1s → call
Retry 2: wait 3s → call (if retry 1 failed)
Retry 3: wait 9s → call (if retry 2 failed)
→ all fail → report to user: "Gateway temporarily unavailable, try again in 1 minute"
```

### 403 — Permission Denied

**Detection:** statusCode=403 or "Forbidden" / "insufficient" in error

**Recovery:** No retry. Report: "Permission denied for this operation. Contact FPR team."

### 500 — Backend Error

**Detection:** statusCode=500 or "Internal Server Error"

**Recovery:** No retry. Report: "Backend error (500). This might be a temporary issue — retry in a moment, or check Datadog."

## Automatic Recovery Summary

| Error | Auto-Retry? | User Prompt? | Action |
|-------|------------|--------------|--------|
| 401 | Yes (after re-auth) | No (silent refresh) | Refresh → retry |
| 400 | Yes (after schema fix) | No (silent schema correction) | Re-search schema → retry |
| 429/503 | Yes (3 times) | No (silent backoff) | Backoff → retry |
| 403 | No | Yes (report) | "Contact FPR team" |
| 500 | No | Yes (report) | "Check Datadog or retry" |

## Non-Retryable Signals

Stop retrying immediately if any of these appear:
- `"not found"` / 404 — tool or endpoint doesn't exist
- `"forbidden"` / 403 — permission, not transient
- Same error message after schema correction (400 case) — not a fixable param issue
- Same error after 3 backoff retries (429/503 case) — not transient
