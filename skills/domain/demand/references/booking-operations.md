# Booking Operations

## get_flight_info / get_flight_info_json
Formatted (or raw JSON) booking details.

**Parameters:** (one required)
- `bookingId`: Traveloka booking ID (**integer**, not string)
- `pnr`: airline PNR code (string)

**Response:** flight segments, passenger names, status, payment summary.

## get_booking_log
Browse booking event logs stored in S3. This is a **file browser** — you navigate directories.

**Parameters:**
- `path` (required): S3 path. Use `/<bookingId>/` to list log files for a booking.
- `date` (optional): `"YYYY-MM-DD"` — narrows the date prefix. If omitted, backend auto-resolves date from bookingId's creation time.

**Usage pattern:**
1. List files: `data: {path: "/1366072360/"}` → returns directory listing
2. Read file: `data: {path: "/1366072360/2026-06-16T06:53:22.006Z_fprfb-submit-booking_request_9e896d.json"}` → returns file content

> ⚠️ The path MUST start with `/`. The backend parses the first path segment as bookingId to resolve dates.
> ⚠️ Do NOT pass `bookingId` as a separate field — it doesn't exist in the schema.

**Response types:**
- DIRECTORY: `objectContent.directoryContents` = list of file paths
- FILE: `objectContent.fileContent` = JSON string of the log entry

**Common log files:**
- `sbf_create_booking_request` — original booking creation (contains search prices vs expected prices)
- `fprfb-submit-booking_request/response` — pricing engine request/response
- `supply-submit-booking-async_request/response` — supply-side booking
- `fprsbook-submit-booking_request/response` — booking service

## search_cache_content
Look up cached fare data for a route.

**Parameters:**
- `origin` (required): airport code, e.g. "CGK"
- `destination` (required): airport code, e.g. "SIN"

> ⚠️ No `departureDate` parameter — shows all cached fares for the route.
> ⚠️ This endpoint may return internal errors for high-traffic routes (known backend limitation).

## Gotchas

- `bookingId` must be passed as **integer** in `get_flight_info`/`get_flight_info_json`
- `get_booking_log` uses `path` not `bookingId` — navigate like a file system
- `search_cache_content` only needs `origin` + `destination`
