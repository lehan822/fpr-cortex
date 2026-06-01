---
name: traveloka-other
description: Other Traveloka platform tools (non-FPR). These are NOT flight pricing tools.
version: "1.0.0"
domain: platform
---

# Other Traveloka Tools

These tools are NOT part of Flight Pricing & Revenue. Do NOT use them for flight pricing queries.

## Operations

| Operation | Domain | Description |
|-----------|--------|-------------|
| `load_hotel_rate_rules` | Hotel | Hotel room rate configuration |
| `get_hotel_commission` | Hotel | Hotel partner commission rates |
| `check_train_fare` | Train | Railway ticket fare check |
| `get_bus_route_pricing` | Bus | Intercity bus fare lookup |
| `load_insurance_premium_rules` | Insurance | Travel insurance premium rules |
| `get_payment_fee_config` | Payment | Payment method surcharge config |
| `load_loyalty_points_rules` | Loyalty | Traveloka Points earning rules |
| `load_voucher_rules` | Promo | Marketing voucher/coupon rules |
| `load_refund_policy_rules` | Refund | Booking refund/cancellation policy |
| `get_ancillary_pricing` | Ancillary | Extra baggage, seat, meal pricing |
| `get_forex_exchange_rate` | Forex | Currency exchange rate lookup |
| `get_pricing_changelog` | Audit | Pricing rule change audit trail |
| `get_alert_config` | Monitoring | Pricing anomaly alert setup |
| `get_competitor_fares` | Competitive | Competitor OTA fare data |
| `get_user_booking_history` | Customer | User past booking records |

## Disambiguation

- "commission" without "hotel" → use FPR `load_commission_incentive_rules`, NOT `get_hotel_commission`
- "fare check" for flights → use FPR `check_fare`, NOT `check_train_fare`
- "fee" for flights → use FPR `load_trx_fee_rules` or `load_issuance_fee_rules`, NOT `get_payment_fee_config`
- "pricing rules" for flights → use FPR `load_baseline_pricing_rules`, NOT `load_hotel_rate_rules`
- "budget" → use FPR `get_budget_balance`, NOT `get_forex_exchange_rate`
