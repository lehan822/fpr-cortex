---
name: fpr-demand
description: Query flight demand data — search simulation, fare cache, user profiling, booking details, promo labels, and winner analysis
version: "1.0.0"
domain: flight-demand
---

# FPR Demand Skill

Demand-side tools for flight search, booking analysis, user profiling, and cache inspection in Traveloka's FPR system.

## Available Operations

| Operation | Description | Key Parameters |
|-----------|-------------|----------------|
| `search_user_profile` | Lookup user personalization profile | userId |
| `load_profiling_config` | Load user profiling configuration | profileType |
| `get_flight_info` | Get booking flight details (formatted) | bookingId, pnr |
| `get_flight_info_json` | Get booking flight details (raw JSON) | bookingId, pnr |
| `get_booking_log` | Get booking event log/history | bookingId |
| `get_winner_details` | Get search winner (selected fare) details | searchId, winnerId |
| `search_winner` | Search winners by route/date | origin, destination, departureDate |
| `simple_crud_query` | MongoDB CRUD query for ad-hoc data lookup | collection, query, database |
| `search_cache_content` | Search fare cache by route | origin, destination, departureDate |
| `search_cache_by_id` | Lookup specific cache entry | searchId |
| `list_mongo_collections` | List available MongoDB collections | database |
| `search_promo_labels` | Search active promo labels | route, airline |
| `get_promo_label_data` | Get supporting data for promo labels | labelId |
| `simulate_search` | Simulate a flight search end-to-end | origin, destination, departureDate, pax |

## Routing Guide

- "search simulation", "simulate flight search", "test search" → `simulate_search`
- "booking detail", "PNR lookup", "booking info" → `get_flight_info`
- "booking log", "booking history", "booking events" → `get_booking_log`
- "fare cache", "cached fares", "cache lookup" → `search_cache_content`
- "cache by search ID" → `search_cache_by_id`
- "winner", "winning fare", "selected result" → `get_winner_details` or `search_winner`
- "user profile", "personalization" → `search_user_profile`
- "profiling config", "profiling rules" → `load_profiling_config`
- "promo label", "promotion tag" → `search_promo_labels`
- "mongo query", "database query", "raw query" → `simple_crud_query`
- "mongo collections", "available tables" → `list_mongo_collections`

## Parameter Normalization

| Parameter | Accepts | Normalized To |
|-----------|---------|--------------|
| origin/destination | "Jakarta", "CGK", "cgk" | "CGK" |
| departureDate | "tomorrow", "2026-06-15" | "YYYY-MM-DD" |

## Disambiguation

- "pricing rules", "markup" → use **fpr-pricing**, NOT demand tools
- "fare adjuster", "fare check" → use **fpr-supply**, NOT `search_cache_content`
- "budget", "budget balance" → use **fpr-pricing** `get_budget_balance`, NOT demand tools
- "booking info" about flight details → `get_flight_info`; about pricing config → **fpr-pricing**
- "search" for flight search simulation → `simulate_search`; for pricing rule search → **fpr-pricing**
