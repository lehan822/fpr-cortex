---
name: fpr-tool-supply
version: 2.5.0
description: "[fprtool] Supply-side tools: fare search (regular/special/upsell), revalidation, search simulation, provider sourcing, fare checking, inventory management, winner selection. Use for supply-side debugging and provider management."
category: fprtool
prerequisites:
  local: [fpr-tool-shared]
  agentcore: []
---

# FPR Supply

> **⚠️ Local MCP tools. All tools are prefixed and authed via fpr-tool-shared — read it first (see Prerequisites).**

```
# Common examples
tool: search_regular_fare           data: {tripType: "ONE_WAY", journeys: [{firstAirport: "CGK", lastAirport: "DPS", departureDate: {month: 6, day: 25, year: 2026}}], numberOfSeats: {numAdults: 1, numChildren: 0, numInfants: 0}, seatClass: "ECONOMY", fareType: "STANDALONE", excludeStale: true}
tool: check_fare                    data: {campaignName: "test", providerContexts: [], airlineId: "GA", specs: []}
tool: get_fare_check_result         data: {executionId: "..."}
tool: simulate_search               data: {tripType: "ONE_WAY", journeys: [{origin: "CGK", destination: "DPS", departureDate: "2026-01-15"}], numAdults: 1, numChildren: 0, numInfants: 0}
```

## Prerequisites — Read Before Executing

**CRITICAL — before the matching operation, you MUST Read the file(s) below. None are optional:**

1. **Local MCP only** → read **fpr-tool-shared** first — auth, tool name prefix, request envelope (**all operations**)
2. **Running fare check** → MUST read [`fare-check-workflow.md`](references/fare-check-workflow.md) (async 2-step operation)
3. **Querying provider config** → MUST read [`provider-operations.md`](references/provider-operations.md)
4. **Inventory staleness issues** → MUST read [`inventory-staleness.md`](references/inventory-staleness.md) (stale filter logic, supplyCacheTimestamp meaning)

**Executing an operation without reading its required reference will cause parameter errors.**

## Operations

| Operation | Description | Key Parameters |
|-----------|-------------|----------------|
| **Fare Search & Revalidation** |||
| `search_regular_fare` | Search regular fare data | tripType, journeys, numberOfSeats, seatClass, fareType, excludeStale |
| `search_special_fare` | Search special/negotiated fare | searchByFlightNumber, richFlightInfo |
| `search_upsell_fare` | Search upsell fare options | UpsellFareSpec |
| `revalidate_regular_fare` | Revalidate regular fare | revalidationJobSpec, revalidationSelectionSpec |
| `revalidate_special_fare` | Revalidate special fare | (see DTO) |
| `revalidate_upsell_fare` | Revalidate upsell fare | (see DTO) |
| **Search Simulation** |||
| `simulate_search` | Simulate end-to-end flight search | tripType, journeys, numAdults, numChildren, numInfants |
| **Provider Management** |||
| `get_provider_sourcing` | Provider sourcing configuration | pagination, filter |
| `get_provider_source_histories` | Provider source history | filter, pagination |
| `get_provider_source_latest_version` | Latest provider source version | — |
| `get_enabled_provider` | Enabled providers for fare checking | — |
| **Fare Checking** |||
| `check_fare` | Trigger fare check (async) | campaignName, providerContexts, airlineId, specs |
| `get_fare_check_result` | Poll fare check result | executionId |
| **Inventory & Special Fare** |||
| `get_special_fare_config` | Special fare configuration | configId |
| `get_inventory_detail` | Detailed inventory breakdown | resultKey |
| `get_inventory_types` | Inventory type definitions | — |
| **Arbitration & Winner** |||
| `get_arbitration_modes` | Arbitration mode settings | — |
| `search_winner` | Search winners by route/date | originAirport, destinationAirport, departureDate, locale |
| **Metadata & Top Pick** |||
| `search_metadata` | Supply metadata | searchQuery |
| `top_pick_crud` | Top pick CRUD operations | action, database, collection, search |

## Routing Guide

| User Intent | → Operation |
|-------------|-------------|
| "search fare", "find fare" | `search_regular_fare`, `search_special_fare`, or `search_upsell_fare` |
| "revalidate fare", "check fare validity" | `revalidate_*_fare` operations |
| "simulate search", "test search pipeline" | `simulate_search` |
| "provider sourcing", "where does fare come from" | `get_provider_sourcing` |
| "check fare", "fare check", "check fare availability" | `check_fare` → `get_fare_check_result` |
| "special fare", "negotiated fare" | `get_special_fare_config` |
| "inventory", "booking class" | `get_inventory_types` or `get_inventory_detail` |
| "winner", "selected fare" | `search_winner` |
| "arbitration", "fare arbitration" | `get_arbitration_modes` |

## Gotchas (top traps — full rules in references)

- **Fare check is async** — must call `check_fare` first, then poll `get_fare_check_result`; see [fare-check-workflow.md](references/fare-check-workflow.md)
- **Inventory staleness filter** — fares older than a threshold may be filtered out; see [inventory-staleness.md](references/inventory-staleness.md)
- **Parameter normalization** — airlineId must be IATA 2-letter uppercase (`"GA"` not `"garuda"`); see table below

## Fare Check Workflow

Fare check is a 2-step async operation:
1. Call `check_fare` → returns `fareCheckId`
2. Poll `get_fare_check_result` with `fareCheckId` (may need 2-3 retries, 5s interval)

See [fare-check-workflow.md](references/fare-check-workflow.md) for full details.

## Parameter Normalization

| Parameter | Accepts | Normalized To |
|-----------|---------|--------------|
| airlineId | "Garuda", "garuda" | `"GA"` (IATA 2-letter) |
| origin/destination | "Jakarta", "CGK", "cgk" | `"CGK"` (IATA 3-letter) |
| departureDate | "tomorrow", "next Monday" | `"YYYY-MM-DD"` |
| tripType | "one way", "round trip" | `"ONE_WAY"`, `"TWO_WAY"`, `"MULTI_CITY"` (enum, use schema values) |

**Note**: Actual required params vary by operation. Always check the schema (Gateway validates types + enum values) before calling. The examples above use the correct schema-extracted field names.

## Disambiguation

- "budget", "commission", "markup" → **fpr-tool-pricing** (not supply)
- "booking detail", "PNR lookup" → **fpr-tool-demand** (not supply)
- "feature flag" → **fpr-tool-sysinteg** (not supply)
- "price inconsistency investigation" → start with **fpr-tool-demand** playbook, then come here for stale filter details
- "airline route history" (reference data) → **fpr-tool-3ps-data**; (provider config) → **fpr-tool-supply**
