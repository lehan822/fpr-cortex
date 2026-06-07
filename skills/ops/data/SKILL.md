---
name: fpr-ops-data
version: "1.0.0"
description: "[ops] BigQuery queries, CDE data pipeline, schema registry, data lake paths for FPR analytics. Use when querying pricing/booking data or debugging data pipelines."
category: ops
prerequisites:
  - fpr-shared
---

# FPR Ops — Data & Analytics

> ⚠️ **Read [fpr-shared](../../gateway/shared/SKILL.md) first** — it covers authentication and environment routing.

## BigQuery Access

### Authentication

```bash
# Use Workload Identity Federation (WIF) — no service account keys
gcloud auth login --update-adc
bq query --project_id=tvlk-data-fpr-stg "SELECT 1"
```

### Key Datasets

| Dataset | Project (stg) | Project (prod) | Description |
|---------|--------------|----------------|-------------|
| `fpr_pricing` | `tvlk-data-fpr-stg` | `tvlk-data-fpr-prd` | Autopilot logs, markup analytics |
| `fpr_demand` | same | same | Booking funnel, search analytics |
| `fpr_supply` | same | same | Provider performance, fare accuracy |
| `fpr_cde` | same | same | CDE activity logs (raw + processed) |

### Common Queries

#### Autopilot rule hit rate (last 7 days)
```sql
SELECT
  rule_id,
  COUNT(*) as hits,
  AVG(margin_bps) as avg_margin
FROM `tvlk-data-fpr-prd.fpr_pricing.autopilot_logs`
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY rule_id
ORDER BY hits DESC
LIMIT 20
```

#### Booking volume by country
```sql
SELECT
  origin_country,
  COUNT(*) as bookings,
  SUM(revenue_usd) as total_revenue
FROM `tvlk-data-fpr-prd.fpr_demand.bookings`
WHERE booking_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
GROUP BY origin_country
ORDER BY bookings DESC
```

## CDE Pipeline (S3 → BigQuery)

### Flow

```
Service logs → Kinesis → S3 (raw) → CDE Ingestion → BigQuery (processed)
```

### S3 Raw Data Paths

```
s3://fpr-cde-raw-{account}/
├── fprtckt/
│   ├── autopilot-logs/dt=YYYY-MM-DD/
│   └── pricing-events/dt=YYYY-MM-DD/
├── fprcpr/
│   └── fare-comparisons/dt=YYYY-MM-DD/
└── fprtool/
    └── activity-logs/dt=YYYY-MM-DD/
```

### Pipeline Health

| Check | Command |
|-------|---------|
| Ingestion lag | Check CDE dashboard for partition freshness |
| Missing partitions | `bq query "SELECT MAX(date) FROM dataset.table"` |
| Schema drift | Compare S3 Parquet schema vs BQ table schema |

## When to Ask User

If the user asks for data not covered above:
1. Ask which metric/dimension they need
2. Ask the time range
3. Ask staging or production
4. Construct query from the appropriate dataset
