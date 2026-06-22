---
name: fpr-supply
version: 2.5.0
description: "Supply-side tools: fare search (regular/special/upsell), revalidation, search simulation, provider sourcing, fare checking, inventory management, winner selection. Use for supply-side debugging and provider management."
category: domain
prerequisites:
  local: [fpr-shared]
  agentcore: []
---

# FPR Supply

> **⚠️ Local MCP tools. All tools are prefixed and authed via fpr-shared — read it first (see Prerequisites).**

```
# Common examples
tool: search_regular_fare           data: {airlineId: "GA", origin: "CGK", destination: "DPS"}
tool: check_fare                    data: {airlineId: "GA", origin: "CGK", destination: "DPS", departureDate: "2026-01-15"}
tool: get_provider_sourcing         data: {airlineId: "GA", origin: "CGK", destination: "DPS"}
tool: simulate_search               data: {origin: "CGK", destination: "DPS", departureDate: "2026-01-15", pax: {adult: 1}}
```

## Prerequisites — Read Before Executing

**CRITICAL — before the matching operation, you MUST Read the file(s) below. None are optional:**

1. **Local MCP only** → read **fpr-shared** first — auth, tool name prefix, request envelope (**all operations**)
2. **Running fare check** → MUST read [`fare-check-workflow.md`](references/fare-check-workflow.md) (async 2-step operation)
3. **Querying provider config** → MUST read [`provider-operations.md`](references/provider-operations.md)
4. **Unsure about parameters** → MUST read [`parameter-standards.md`](references/parameter-standards.md) (airlineId IATA format, origin/destination codes)

**Executing an operation without reading its required reference will cause parameter errors.**

## Operations

| Operation | Description | Key Parameters |
|-----------|-------------|----------------|
| **Fare Search & Revalidation** |||
| `search_regular_fare` | Search regular fare data | airlineId, origin, destination |
| `search_special_fare` | Search special/negotiated fare | airlineId, origin, destination |
| `search_upsell_fare` | Search upsell fare options | airlineId, origin, destination |
| `revalidate_regular_fare` | Revalidate regular fare | airlineId, origin, destination, departureDate |
| `revalidate_special_fare` | Revalidate special fare | airlineId, origin, destination, departureDate |
| `revalidate_upsell_fare` | Revalidate upsell fare | airlineId, origin, destination, departureDate |
| **Search Simulation** |||
| `simulate_search` | Simulate end-to-end flight search | origin, destination, departureDate, pax |
| **Provider Management** |||
| `get_provider_sourcing` | Provider sourcing configuration | airlineId, origin, destination |
| `get_provider_source_histories` | Provider source history | providerSourceId |
| `get_provider_source_latest_version` | Latest provider source version | providerSourceId |
| `get_enabled_provider` | Enabled providers for fare checking | — |
| `save_provider_source` | Save provider source (write) | providerSourceData |
| `import_provider_source` | Import provider source (write) | providerSourceData |
| `remove_provider` | Remove provider (write) | providerId |
| **Fare Checking** |||
| `check_fare` | Trigger fare check (async) | airlineId, origin, destination, departureDate |
| `get_fare_check_result` | Poll fare check result | fareCheckId |
| `upload_fare_checking_csv` | Upload fare checking CSV (write) | csvData |
| **Inventory & Special Fare** |||
| `get_special_fare_config` | Special fare configuration | airlineId |
| `get_inventory_detail` | Detailed inventory breakdown | airlineId, flightNumber |
| `get_inventory_types` | Inventory type definitions | — |
| **Arbitration & Winner** |||
| `get_arbitration_modes` | Arbitration mode settings | airlineId |
| `search_winner` | Search winners by route/date | origin, destination, departureDate |
| **Metadata & Top Pick** |||
| `search_metadata` | Supply metadata | filters |
| `top_pick_crud` | Top pick CRUD operations | operation, data |

## Routing Guide

| User Intent | → Operation |
|-------------|-------------|
| "search fare", "find fare" | `search_regular_fare`, `search_special_fare`, or `search_upsell_fare` |
| "revalidate fare", "check fare validity" | `revalidate_*_fare` operations |
| "simulate search", "test search pipeline" | `simulate_search` |
| "provider sourcing", "where does fare come from" | `get_provider_sourcing` |
| "fare check", "check fare availability" | `check_fare` → `get_fare_check_result` |
| "special fare", "negotiated fare" | `get_special_fare_config` |
| "inventory", "booking class" | `get_inventory_types` or `get_inventory_detail` |
| "winner", "selected fare" | `search_winner` |
| "arbitration", "fare arbitration" | `get_arbitration_modes` |

## Gotchas (top traps — full rules in references)

- **Fare check is async** — must call `check_fare` first, then poll `get_fare_check_result`; see [fare-check-workflow.md](references/fare-check-workflow.md)
- **Parameter normalization** — airlineId must be IATA 2-letter uppercase (`"GA"` not `"garuda"`); see [parameter-standards.md](references/parameter-standards.md)

## Fare Check Workflow

Fare check is a 2-step async operation:
1. Call `check_fare` → returns `fareCheckId`
2. Poll `get_fare_check_result` with `fareCheckId` (may need 2-3 retries, 5s interval)

See [fare-check-workflow.md](references/fare-check-workflow.md) for full details.

## Disambiguation

- "budget", "commission", "markup" → **fpr-pricing** (not supply)
- "booking detail", "PNR lookup" → **fpr-demand** (not supply)
- "feature flag" → **fpr-sysinteg** (not supply)
- "price inconsistency investigation" → **fpr-demand** (booking logs, fare comparison)
- "airline route history" (reference data) → **fpr-3ps-datainfo**; (provider config) → **fpr-supply**
