---
name: fpr-supply
description: "[domain] fare adjusters, provider configuration, airline routes, search metadata, provider sourcing, fare checking, inventory types. Use for supply-side debugging and provider management."
version: "2.0.0"
category: domain
domain: supply
prerequisites:
  - fpr-shared
---

# FPR Supply

> ⚠️ **Tool name prefix required:** When calling `tools/call`, prepend `fprtool-backend___` to every operation name below. Params go inside `data:{}` envelope. See fpr-shared for full request format.

## 前置条件 — 执行操作前必读

**CRITICAL — 执行对应操作前，MUST 先读取以下文件：**
1. [`fpr-shared`](../../shared/auth/SKILL.md) — 认证、Gateway 协议、error handling（所有操作通用）
2. **执行 fare check** → 必读 [`fare-check-workflow.md`](references/fare-check-workflow.md)（异步 2 步操作）
3. **查询 provider 配置** → 必读 [`provider-operations.md`](references/provider-operations.md)

**未读完以上文件就执行相应操作会导致流程错误。**

## Operations

| Operation | Description | Key Parameters |
|-----------|-------------|----------------|
| `load_fare_adjuster_by_base_fare` | Fare adjuster rules (base fare) | airlineId, origin, destination |
| `load_fare_adjuster_by_airport_tax` | Fare adjuster rules (airport tax) | airlineId, origin, destination |
| `read_pricing_provider` | Provider configuration & routing | providerId |
| `check_fare` | Trigger fare check (async) | airlineId, origin, destination, departureDate |
| `get_fare_check_result` | Poll fare check result | fareCheckId |
| `get_special_fare_config` | Special/negotiated fare config | airlineId |
| `search_regular_fare` | Search regular fare data | airlineId, origin, destination |
| `get_airline_routes` | Active routes for airline | airlineId |
| `get_airline_route_history` | Route activation/deactivation history | airlineId, origin, destination |
| `get_provider_sourcing` | Provider sourcing configuration | airlineId, origin, destination |
| `get_arbitration_modes` | Arbitration mode settings | airlineId |
| `get_inventory_types` | Inventory type definitions | — |
| `get_inventory_detail` | Detailed inventory breakdown | airlineId, flightNumber |

## Routing Guide

| User Intent | → Operation |
|-------------|-------------|
| "fare adjuster", "adjustment rules" | `load_fare_adjuster_by_base_fare` or `_airport_tax` |
| "provider config", "provider routing" | `read_pricing_provider` |
| "fare check", "check fare availability" | `check_fare` → `get_fare_check_result` |
| "special fare", "negotiated fare" | `get_special_fare_config` |
| "regular fare", "published fare" | `search_regular_fare` |
| "airline routes", "active routes" | `get_airline_routes` |
| "route history", "when did route start" | `get_airline_route_history` |
| "provider sourcing", "where does fare come from" | `get_provider_sourcing` |
| "arbitration", "fare arbitration" | `get_arbitration_modes` |
| "inventory type", "booking class" | `get_inventory_types` or `get_inventory_detail` |

## Fare Check Workflow

Fare check is a 2-step async operation:
1. Call `check_fare` → returns `fareCheckId`
2. Poll `get_fare_check_result` with `fareCheckId` (may need 2-3 retries, 5s interval)

## Parameter Normalization

| Parameter | Accepts | Normalized To |
|-----------|---------|--------------|
| airlineId | "Garuda", "garuda" | `"GA"` |
| origin/destination | "Jakarta", "CGK", "cgk" | `"CGK"` (IATA 3-letter) |
| departureDate | "tomorrow", "next Monday" | `"YYYY-MM-DD"` |
| providerId | numeric string | `"123"` |

## Disambiguation

- "budget", "commission", "markup" → **fpr-pricing** (not supply)
- "booking detail", "PNR lookup" → **fpr-demand** (not supply)
- "feature flag" → **fpr-config** (not supply)
