# Fare Check Workflow

## Overview
Fare check verifies real-time availability and price from the airline GDS.

## Step 1: Initiate
```
Operation: check_fare
Parameters: airlineId, origin, destination, departureDate, cabinClass (optional)
Returns: { fareCheckId: "fc-abc123", status: "PENDING" }
```

## Step 2: Poll Result
```
Operation: get_fare_check_result
Parameters: fareCheckId
Returns: { status: "COMPLETED"|"PENDING"|"FAILED", fares: [...] }
```

**Polling strategy:** Wait 5 seconds between retries, max 3 attempts.

## Error Handling
- `TIMEOUT`: GDS didn't respond in 30s — retry once
- `NO_FARE`: Route exists but no availability on date
- `INVALID_ROUTE`: Route doesn't exist in airline network
