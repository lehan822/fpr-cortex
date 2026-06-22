# Inventory Staleness

## Key Concept: supplyCacheTimestamp

`supplyCacheTimestamp` in demand tracking logs = `AirlineRouteData.lastUpdatedTime` in Sinan inventory store.

This is when the **supply scraper last wrote** this inventory record — NOT when demand cached it.

Code path:
```
FlightSearchTrackingBuilder.getEarliestSupplyCacheTimestamp()
  → FlightRouteCWithInventory.getSupplyLastUpdatedTimestamp()
    → AirlineRouteData.getLastUpdatedTime()
```

## StaleInventoryRejector

Location: `fpr-route-search-backend` → `flight-route-impl/.../sinan/rejector/StaleInventoryRejector.java`

### Logic

```java
boolean isFetchedItemStale(fetchedItem, pollStartTime) {
    TimeToStale timeToStale = liveService.getTimeToStale(provider, route);
    return fetchedItem.getTimestamp() < (pollStartTime - timeToStale.inMillis());
}
```

`timeToStale` is dynamic per provider/route, sourced from `LiveFetchTimeToStaleService`.

### Activation Conditions (ALL must be true)

1. `USE_STALE_REJECTOR_FEATURE` feature flag is enabled
2. `staleInventoryPolicy` = `EXCLUDE_STALE_INVENTORY` (set when `excludeStale=true`)
3. Provider is NOT of type DATAFEED (datafeed is exempt)
4. Provider is not in the rejector blacklist

### Where excludeStale is set

`excludeStale` defaults to **false** in `FlightSpecFilter`. It is set to `true` only when:

1. **Inventory Refresh V2 mode** — hybrid search with live fetch
2. **FlightSupplyFilterConfig** — per route/agent configuration
   - Source: `FlightSupplyFilterConfigHelper.java` in `fpr-fprcinv`
   - Config dimensions: route (origin+destination), agentType, agentId

### Implications for Oncall

- If `supplyCacheTimestamp` is very old (hours/days) and data was still served to demand, it means:
  - The scraper hasn't updated this provider+route record in Sinan
  - AND `excludeStale` was not enabled for this route (no FlightSupplyFilterConfig entry)
  - OR the provider is classified as DATAFEED (exempt from rejection)

- The **booking selection flow** does NOT go through StaleInventoryRejector — it only logs "LUT_INVESTIGATION diff more than 12 hours"

## Common Providers

| Provider | Type | Notes |
|----------|------|-------|
| amadeusEDI | GDS | Full service, stale filter applies if enabled |
| didaMI | Aggregator | Usually fresh (frequent scraping) |
| DATAFEED providers | DATAFEED | Exempt from stale rejection |

## Demand-Side Cache (NOT the staleness source)

Demand Redis search cache TTL = 10 minutes (`CacheSSOT.TWOWAY_CACHE_TIMEOUT_MS = 600_000`).

If `supplyCacheTimestamp` is older than 10 minutes relative to `demandRequestTimestamp`, the staleness is from Sinan inventory (supply side), NOT from demand cache.
