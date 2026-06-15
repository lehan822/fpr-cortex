---
name: fpr-demand
description: "Booking lookup, user profiles, fare cache, search simulation, promo labels, MongoDB queries. Use for demand-side debugging — bookings, search results, user segments."
version: "2.2.0"
category: domain
domain: demand
prerequisites:
  local: [fpr-shared]
  agentcore: []
tools:
  - get_booking_log
  - get_demand_experiment_contextid
  - get_demand_experiment_variant
  - get_flight_info
  - get_flight_info_json
  - get_promo_label_data
  - get_promo_label_detail
  - get_winner_details
  - list_mongo_collections
  - load_profiling_config
  - search_cache_by_id
  - search_cache_content
  - search_promo_labels
  - search_user_profile
  - search_winner
  - simple_crud_query
---

# FPR Demand

## Prerequisites — Read Before Executing

1. **Local MCP only** → read **fpr-shared** first (auth, tool name prefix, request envelope)
2. **Running search simulation** → MUST read [`search-simulation.md`](references/search-simulation.md) (full pipeline parameters)
3. **Querying bookings** → MUST read [`booking-operations.md`](references/booking-operations.md) (bookingId vs PNR distinction)

**Executing operations without reading the required references will lead to parameter or workflow errors.**

## Operations

| Operation | Description | Key Parameters |
|-----------|-------------|----------------|
| `search_user_profile` | Lookup user personalization profile | userId |
| `load_profiling_config` | User profiling configuration | profileType |
| `get_flight_info` | Booking flight details (formatted) | bookingId or pnr |
| `get_flight_info_json` | Booking flight details (raw JSON) | bookingId or pnr |
| `get_booking_log` | Booking event log / timeline | bookingId |
| `get_winner_details` | Search winner (selected fare) | searchId, winnerId |
| `search_winner` | Find winners by route/date | origin, destination, departureDate |
| `simple_crud_query` | MongoDB ad-hoc query | collection, query, database |
| `search_cache_content` | Fare cache by route | origin, destination, departureDate |
| `search_cache_by_id` | Specific cache entry | searchId |
| `list_mongo_collections` | Available MongoDB collections | database |
| `search_promo_labels` | Active promo labels | route, airline |
| `get_promo_label_data` | Promo label supporting data | labelId |
| `simulate_search` | Simulate end-to-end flight search | origin, destination, departureDate, pax |

## Routing Guide

| User Intent | → Operation |
|-------------|-------------|
| "search simulation", "test search" | `simulate_search` |
| "booking detail", "PNR lookup" | `get_flight_info` |
| "booking log", "booking history" | `get_booking_log` |
| "fare cache", "cached fares" | `search_cache_content` |
| "winner", "winning fare" | `get_winner_details` or `search_winner` |
| "user profile", "personalization" | `search_user_profile` |
| "promo label", "promotion tag" | `search_promo_labels` |
| "mongo query", "raw query" | `simple_crud_query` |

## Search Simulation Notes

`simulate_search` runs the full search pipeline end-to-end. Useful for:
- Debugging "why does this route show no results"
- Verifying price changes take effect
- Testing promo label visibility

Returns: ranked fares with applied pricing, provider info, and promo labels.

## Parameter Normalization

| Parameter | Accepts | Normalized To |
|-----------|---------|--------------|
| origin/destination | "Jakarta", "CGK", "cgk" | `"CGK"` |
| departureDate | "tomorrow", "next Monday" | `"YYYY-MM-DD"` |
| pax | "2 adults", "1a1c" | `{ adult: 2, child: 0, infant: 0 }` |
| bookingId / pnr | string | as-is |

## Disambiguation

- "markup", "commission", "budget" → **fpr-pricing** (not demand)
- "fare adjuster", "provider config" → **fpr-supply** (not demand)
- "feature flag", "country list" → **fpr-config** (not demand)
