# Booking Operations

## get_flight_info
Formatted booking details — human-readable summary.

**Parameters:** (one required)
- `bookingId`: Traveloka booking ID
- `pnr`: airline PNR code

**Response:** flight segments, passenger names, status, payment summary.

## get_booking_log
Timeline of booking events from creation to completion.

**Parameters:**
- `bookingId` (required)

**Response:** ordered list of events (CREATED → CONFIRMED → TICKETED → etc.)
with timestamps and metadata.
