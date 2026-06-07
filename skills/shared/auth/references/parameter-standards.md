# Parameter Standards & Error Handling

## Common Parameters

| Parameter | Format | Examples | Notes |
|-----------|--------|----------|-------|
| country | ISO 3166-1 alpha-2 | ID, TH, VN, MY, SG, AU | |
| currency | ISO 4217 | IDR, THB, VND, MYR, SGD, AUD | |
| profileGroup | Enum | TRAVELOKA, AFFILIATE, CORPORATE | ⚠️ NOT a country code |
| originCountry | ISO 3166-1 alpha-2 | TH, ID, VN | Use for country filtering |
| airlineId | IATA 2-letter | GA, QZ, VJ, TG | |
| fulfillmentId | Internal ID | (varies) | |

### Important Distinctions

- **profileGroup** is an enum (`TRAVELOKA` / `AFFILIATE` / `CORPORATE`), NOT a country code
- Use **originCountry** for country-based filtering (e.g., "TH" for Thailand rules)
- These two fields are commonly confused — always double-check

## Error Handling

| HTTP Code | Meaning | Agent Action |
|-----------|---------|-------------|
| 401 | User token expired | Run the PKCE login flow again |
| 403 | Insufficient permissions | Inform user: "Additional permissions required; contact FPR team" |
| 404 | Operation not found | Check operation name (must include `fprtool-backend___` prefix) |
| 429 | Rate limited | Retry with backoff (5s, 10s, 20s) |
| 500 | Backend error | Report error, suggest retry |

## Incomplete Parameters Strategy

When a user's request doesn't include all required parameters:

1. **Use sensible defaults** where safe:
   - `profileGroup` → `TRAVELOKA` (most common)
   - Environment → `staging` (safer for exploration)
2. **State your assumption** to the user: "Using profileGroup=TRAVELOKA, staging env"
3. **Ask the user** if a parameter has no safe default and multiple valid options
