# Price Inconsistency Investigation Playbook

Use this when a customer reports a price jump between search and booking submission.

## Step-by-Step Workflow

### Step 1: Confirm booking details (FPR MCP)

```
Operation: get_flight_info_json
Params: bookingId (integer)
```

Extract: route, airline, provider, departure date, seat class, booking time.

### Step 2: Get fare discrepancy from booking log (FPR MCP)

```
Operation: get_booking_log
Params: path: "/<bookingId>/"   → lists available log files
        path: "/<bookingId>/sbf_create_booking_request"  → shows actual request
```

Key fields in sbf_create_booking_request:
- `farePerPaxSearch` — fare shown to user during search
- `farePerPaxExpected` — fare at booking submission (reprice result)
- `subclass` — cabin class at booking time

If `farePerPaxSearch ≠ farePerPaxExpected`, price inconsistency is confirmed.

### Step 3: Get searchId

From the booking log or from the team (e.g., Vincent provided it in chat). The searchId links search → summary_tray → booking.

### Step 4: Query fprbopi price-accuracy-tracking (Datadog)

```
Service: fprbopi
Query: @searchId:<searchId>
Storage: flex_and_indexes (REQUIRED — hot indexes may not retain data)
Time range: use ISO 8601, bracket the booking time ±3h
Extra fields:
  - funnelAfter, funnelBefore
  - supplyCacheTimestamp.before, supplyCacheTimestamp.after
  - demandRequestTimestamp.before, demandRequestTimestamp.after
  - farePerPax.before, farePerPax.after
  - subclass.before, subclass.after
  - providerId.before, providerId.after
```

This shows how the fare changed at each funnel step (SEARCH_RESULT → SUMMARY_TRAY → SUBMIT_BOOKING).

### Step 5: Interpret supplyCacheTimestamp

`supplyCacheTimestamp` = `AirlineRouteData.lastUpdatedTime` in Sinan inventory store.

Code path:
```
FlightSearchTrackingBuilder.getEarliestSupplyCacheTimestamp()
  → FlightRouteCWithInventory.getSupplyLastUpdatedTimestamp()
    → AirlineRouteData.getLastUpdatedTime()
```

This is when the **supply scraper last wrote** this inventory record to Sinan — NOT when demand cached it.

**Staleness check:** `demandRequestTimestamp - supplyCacheTimestamp` = how old the supply data was when the user searched.

### Step 6: Determine root cause

| Pattern | Root Cause |
|---------|-----------|
| `supplyCacheTimestamp` is old (hours/days), same before/after | Supply scraper hasn't refreshed this provider+route |
| `subclass` changes between funnels | Availability changed — original class sold out, upgraded |
| `supplyCacheTimestamp.after` is fresh but `subclass` changed | Live availability check found different inventory |
| Different `providerId` before/after | Provider switch during reprice |

### Step 7: Check stale filter status

If supply data is stale, check why `StaleInventoryRejector` didn't filter it:
- `excludeStale` defaults to `false` — only enabled via `FlightSupplyFilterConfig` per route
- DATAFEED providers are exempt from stale rejection
- Booking selection flow does NOT use StaleInventoryRejector (only logs)

Relevant code: `fpr-route-search-backend` → `StaleInventoryRejector.java`

## Key Services in Datadog

| Service | Role |
|---------|------|
| `fprbopi` | Price accuracy tracking (funnel transitions) |
| `fprbook` | Booking service (REPRICE logs) |
| `fprbpf` | Mainflow / search continuation |
| `fprtool` | FPR tool backend (MCP gateway) |
| `fprcinv` | Demand inventory search (Redis cache layer) |

## Common Gotchas

1. **Use `flex_and_indexes` storage tier** — hot indexes only retain recent data (hours), flex has days
2. **`time_period` vs `from`/`to`** — for precise investigation, always use ISO 8601 `from`/`to` timestamps
3. **searchId may not appear in route-search/Sinan logs** — those services don't always log the demand searchId; use fprbopi instead
4. **Demand Redis cache TTL is 10 minutes** (`CacheSSOT.TWOWAY_CACHE_TIMEOUT_MS = 600_000`) — if staleness > 10min, it's NOT demand cache
