# Provider Operations

## read_pricing_provider
Full provider configuration including routing rules, priority, and capabilities.

**Parameters:**
- `providerId` (required): numeric provider ID

**Response includes:**
- Provider name, type (GDS/NDC/LCC)
- Supported airlines
- Routing priority
- Rate limits
- Health status

## get_provider_sourcing
Which provider supplies fares for a specific route.

**Parameters:**
- `airlineId`, `origin`, `destination` (all required)

**Response:** ranked list of providers with priority scores.
