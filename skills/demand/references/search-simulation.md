# Search Simulation

## simulate_search
Runs the full flight search pipeline end-to-end, exactly as a user would experience.

**Parameters:**
- `origin` (required): IATA code (e.g. "CGK")
- `destination` (required): IATA code (e.g. "DPS")
- `departureDate` (required): "YYYY-MM-DD"
- `pax` (optional): { adult: 1, child: 0, infant: 0 }

**What it does:**
1. Queries all active providers for the route
2. Applies fare adjusters and pricing rules
3. Applies promo labels and budget discounts
4. Ranks results by price
5. Returns final search results page

**Use cases:**
- "Why does CGK-DPS show no results on June 20?"
- "What price does a user see for GA Jakarta-Bali?"
- "Is my new pricing rule applied?"

**Response:** Array of ranked fares with breakdown (base, tax, markup, discount, final).
