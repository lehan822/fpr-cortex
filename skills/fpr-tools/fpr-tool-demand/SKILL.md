---
name: fpr-tool-demand
version: 2.6.0
description: "[fprtool] Demand-side tools: booking lookup, fare cache, demand experiments, MongoDB queries. Use for demand-side debugging — bookings, search results, user experiments."
category: fprtool
prerequisites:
  local: [fpr-tool-shared]
  agentcore: []
---

# FPR Demand

> **⚠️ Local MCP tools. All tools are prefixed and authed via fpr-tool-shared — read it first (see Prerequisites).**

```
# Common examples
tool: get_flight_info                  data: {bookingId: 1365484156}
tool: search_cache_content             data: {searchId: "..."}
tool: get_booking_log                  data: {date: "2026-06-23", path: "/123456789/"}
```

## Prerequisites — Read Before Executing

**CRITICAL — before the matching operation, you MUST Read the file(s) below. None are optional:**

1. **Local MCP only** → read **fpr-tool-shared** first — auth, tool name prefix, request envelope (**all operations**)
2. **Querying bookings** → MUST read [`booking-operations.md`](references/booking-operations.md) (bookingId vs PNR distinction)
3. **Price inconsistency oncall** → MUST read [`price-inconsistency-playbook.md`](references/price-inconsistency-playbook.md) (end-to-end investigation workflow)

**Executing an operation without reading its required reference will cause parameter errors.**

## Operations

| Operation | Description | Key Parameters |
|-----------|-------------|----------------|
| **Fare Cache** |||
| `search_cache_content` | Fare cache by route | origin, destination |
| `search_cache_by_id` | Specific cache entry | searchId |
| **Demand Experiments** |||
| `get_demand_experiment_variant` | Get experiment variant | namespace, userId |
| `get_demand_experiment_contextid` | Get experiment context by ID | contextId |
| **MongoDB Operations** |||
| `list_mongo_collections` | Available MongoDB collections | database |
| `simple_crud_query` | MongoDB ad-hoc query | collection, query, database |
| **Booking Details** |||
| `get_flight_info` | Booking flight details (formatted) | bookingId or pnr |
| `get_flight_info_json` | Booking flight details (raw JSON) | bookingId or pnr |
| `get_booking_log` | Booking event log / timeline | path: `/<bookingId>/` |
| **Promo Labels** |||
| `search_promo_labels` | Search/list promo labels | airlineId, filters |
| `get_promo_label_data` | Promo label supporting data/options | — |
| `get_promo_label_detail` | Promo label detail | promoLabelId |
| `create_promo_label` | Create promo label (write) | promoLabelData |
| `update_promo_label` | Update promo label (write) | promoLabelId, promoLabelData |
| **Booking Operations (Write)** |||
| `update_passenger_detail` | Update passenger details (write) | bookingId, passengerData |
| `mark_issued_send_eticket` | Mark issued and send e-ticket (write) | bookingId |
| `resend_eticket` | Resend e-ticket (write) | bookingId |

## Routing Guide

| User Intent | → Operation |
|-------------|-------------|
| "booking", "booking detail", "PNR lookup" | `get_flight_info` |
| "booking log", "booking history" | `get_booking_log` |
| "fare cache", "cached fares" | `search_cache_content` |
| "promo label", "promo labels", "active promo labels" | `search_promo_labels` |
| "experiment variant", "A/B test" | `get_demand_experiment_variant` |
| "mongo query", "raw query" | `simple_crud_query` |

## Gotchas (top traps — full rules in references)

- **bookingId MUST be integer** — not string; `123456789` not `"123456789"`
- **PNR vs bookingId** — PNR is airline reference (string), bookingId is Traveloka internal (integer); see [booking-operations.md](references/booking-operations.md)
- **Price inconsistency oncall** — follow the full playbook in [price-inconsistency-playbook.md](references/price-inconsistency-playbook.md)

## Oncall Scenarios

| User Intent | → Workflow |
|-------------|------------|
| "price jump at booking", "price inconsistency" | See [price-inconsistency-playbook.md](references/price-inconsistency-playbook.md) |
| "why did subclass change" | `get_booking_log` → Datadog fprbopi funnel |
| "stale supply data", "old cache" | Check `supplyCacheTimestamp` in fprbopi logs |

## Disambiguation

- "markup", "commission", "budget" → **fpr-tool-pricing** (not demand)
- "fare adjuster", "provider config", "provider sourcing" → **fpr-tool-supply** (not demand)
- "feature flag", "country list" → **fpr-tool-sysinteg** (not demand)
- "simulate search" → **fpr-tool-supply** (not demand)

## Note

`simulate_search` has been moved to **fpr-tool-supply** as it's a supply-side operation that simulates the search pipeline.
