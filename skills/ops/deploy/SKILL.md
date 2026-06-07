---
name: fpr-ops-deploy
version: "1.0.0"
description: "[ops] CI/CD pipelines, CodeDeploy, canary deployment, rollback procedures for FPR services. Use when deploying, checking deployment status, or rolling back."
category: ops
prerequisites:
  - fpr-shared
---

# FPR Ops — Deployment

> ⚠️ **Read [fpr-shared](../../gateway/shared/SKILL.md) first** — it covers authentication and environment routing.

## Service Deployment Matrix

| Service | Tool | Trigger | sstg | fstg | prod |
|---------|------|---------|------|------|------|
| fprtckt | CodeDeploy | Merge to `master` | Auto (30min approval) | N/A | Manual promote |
| fprcpr | B-Flow | Merge to `master` | Auto | N/A | Manual promote |
| fprtool-backend | B-Flow | Merge to `master` / push to `dev` | Auto (master) | Auto (dev) | Manual promote |
| fpr-cortex | GitHub Actions | Push to `main` / `release` | Auto (main) | N/A | Auto (release) |

## Deployment Flows

### fprtckt (CodeDeploy)

```
PR merged → CodeDeploy starts → Install → AllowTraffic (30min window) → Done
```

⚠️ **Must manually approve "Reroute Traffic" step in CodeDeploy console within 30 minutes**, otherwise deployment rolls back.

### fprtool-backend (B-Flow)

```
PR merged to master → B-Flow auto-deploys to sstg
Push to dev branch  → B-Flow auto-deploys to fstg
```

### fpr-cortex (Skills)

```
Push to main   → CI: generate schema → upload to S3 (stg) → register in AgentCore
Push to release → CI: same flow for prod
```

## Rollback

| Service | How |
|---------|-----|
| fprtckt | CodeDeploy console → Stop & Rollback, or redeploy previous commit |
| fprcpr | Revert PR + merge to master |
| fprtool-backend | Revert PR + merge, or B-Flow manual rollback |

## Health Checks After Deploy

| Service | Check |
|---------|-------|
| fprtckt | Datadog dashboard `FPR fprtckt`, memory < 85%, no OOM |
| fprcpr | cleanSweep E2E passes, Karate tests green |
| fprtool-backend | `/health` endpoint 200, API latency p99 < 2s |

## Common Issues

| Problem | Fix |
|---------|-----|
| CodeDeploy stuck at "Reroute traffic" | Click approve in console (30min timeout) |
| cleanSweep blocking deploys | sstg flight search empty — check fprtckt/fprcpr health |
| B-Flow deploy fails "artifact not found" | Check if Gradle build succeeded in CI |
| fprtckt OOM after deploy | Memory at 98% — scale up or rollback immediately |
