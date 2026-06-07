---
name: fpr-ops-infra
version: "1.0.0"
description: "[ops] S3 bucket paths, BQ datasets, DynamoDB tables, Redis clusters for FPR services. Use when looking up resource locations or debugging data storage issues."
category: ops
prerequisites:
  - fpr-shared
---

# FPR Ops — Infrastructure Resources

> ⚠️ **Read [fpr-shared](../../gateway/shared/SKILL.md) first** — it covers authentication and environment routing.

## S3 Buckets

| Bucket Pattern | Content | Example |
|----------------|---------|---------|
| `fpr-fprtckt-rules-ap-southeast-1-{account}-{hash}` | Autopilot/pricing rules JSON | `fpc.autopilot/TRAVELOKA.DEFAULT.STANDALONE/` |
| `fpr-fprcpr-*` | Fare comparison data | |
| `fpr-cortex-skills-*` | Skill distribution (CI/CD) | |

### Bucket by Environment

| Env | Account ID | Profile |
|-----|-----------|---------|
| sstg/fstg | `354767975881` | `Engineer@tvlk-fpr-stg` |
| prod | `474532148129` | `Engineer@tvlk-fpr-prd` |

## DynamoDB Tables

| Table | Service | Key Schema |
|-------|---------|------------|
| `fprtckt-rules-*` | fprtckt | partitionKey: ruleType, sortKey: ruleId |
| `fprtool-*` | fprtool-backend | varies by feature |

## BigQuery Datasets

| Dataset | Content | Project |
|---------|---------|---------|
| `fpr_pricing` | Pricing analytics, autopilot logs | `tvlk-data-fpr-stg` / `tvlk-data-fpr-prd` |
| `fpr_demand` | Booking/search analytics | same |
| `fpr_supply` | Provider performance, fare data | same |

## Redis Clusters

| Cluster | Service | Access |
|---------|---------|--------|
| `fprtckt-cache` | fprtckt | Bastion via `tvlk-fpr-stg` VPC |
| `fprcpr-cache` | fprcpr | Same bastion |

### Bastion Access

```bash
# Connect to Redis via bastion (staging)
ssh -L 6379:{redis-endpoint}:6379 bastion-fpr-stg
redis-cli -h localhost -p 6379
```

## When to Ask User

If the user asks about a resource not listed above:
1. Ask which service it belongs to (fprtckt / fprcpr / fprtool)
2. Ask which environment (staging / production)
3. Search using AWS CLI with the appropriate profile
