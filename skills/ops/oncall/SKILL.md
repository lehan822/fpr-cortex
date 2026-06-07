---
name: fpr-ops-oncall
version: "1.0.0"
description: "[ops] On-call runbooks, error code reference, escalation paths, common incident patterns for FPR services. Use when debugging production issues or responding to alerts."
category: ops
prerequisites:
  - fpr-shared
---

# FPR Ops — On-Call & Incident Response

> ⚠️ **Read [fpr-shared](../../gateway/shared/SKILL.md) first** — it covers authentication and environment routing.

## Escalation Path

```
Alert fired → On-call engineer → Team lead (15min no response) → Arshad (P1 only)
```

## Common Alerts & Runbooks

### fprtckt Memory High (>90%)

**Symptom:** Datadog alert "fprtckt memory usage critical"

**Steps:**
1. Check Datadog: `FPR fprtckt` dashboard → Memory panel
2. If >95%: immediately scale up instances or rollback last deploy
3. If 90-95%: check for recent rule changes that inflated cache
4. Root cause: usually large autopilot rule set loaded into memory

### fprcpr Fare Mismatch

**Symptom:** cleanSweep E2E failures, fare comparison returning stale data

**Steps:**
1. Check fprcpr cache freshness (Redis TTL)
2. Verify provider endpoints responding (supply health)
3. If provider down → enable fallback in feature flags

### Search Returns Empty Results (sstg)

**Symptom:** cleanSweep, Karate tests failing with empty search results

**Steps:**
1. Check fprtckt health — is it OOM/restarting?
2. Check fprcpr health — fare data available?
3. Check feature flags — any kill switch accidentally enabled?
4. Check recent deploys — did someone deploy broken rules?

## Error Code Reference

| Code | Service | Meaning | Action |
|------|---------|---------|--------|
| `PRICING_RULE_NOT_FOUND` | fprtckt | No matching rule for request | Check rule S3 bucket has data for that country/airline |
| `BUDGET_EXHAUSTED` | fprtckt | Budget limit reached | Check budget balance, may need top-up |
| `PROVIDER_TIMEOUT` | fprcpr | Upstream provider slow | Check provider status, consider increasing timeout |
| `FARE_CACHE_MISS` | fprcpr | No cached fare available | Trigger cache refresh or check Redis |

## Datadog Dashboards

| Dashboard | URL Pattern | Purpose |
|-----------|-------------|---------|
| FPR fprtckt | `app.datadoghq.com/dashboard/xxx` | Service health, memory, latency |
| FPR fprcpr | `app.datadoghq.com/dashboard/yyy` | Fare comparison metrics |
| FPR Price Prediction | `app.datadoghq.com/dashboard/zzz` | PP model accuracy, hit rate |

## When to Ask User

If an alert or error isn't covered above:
1. Ask which service is affected
2. Ask for the exact error message or alert name
3. Check Datadog logs with the service + error context
