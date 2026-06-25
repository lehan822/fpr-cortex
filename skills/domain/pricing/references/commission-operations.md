# Commission & Incentive Operations

## load_commission_incentive_rules
Commission rates for airline partners.

**Parameters:**
- `airlineId` (required): IATA code (e.g. "GA")
- `fulfillmentId` (optional): specific fulfillment channel

**Response:** Array of commission rules with rate, effective dates, conditions.

## load_tiered_incentive_rules
Volume-based bonus tiers (e.g. "100+ bookings = 2% extra").

**Parameters:**
- `brandId` (required): airline brand identifier

## check_tiered_incentive_progress
Check how close a PNR's airline is to hitting next tier.

**Parameters:**
- `pnr` (required): booking PNR code
