# Operation Catalog

> Auto-generated — do not edit manually.
> Run: `python scripts/generate-catalog.py`

**Total: 64 operations** across 1 backend(s): fprtool

| operationId | Description | Domain |
|---|---|---|
| `check_fare` | Check fare | supply |
| `check_tiered_incentive_progress` | Check incentive progress for a booking | pricing |
| `convert_currency` | Convert currency | config |
| `get_activity_log` | Get Activity/Audit Log | config, pricing |
| `get_airline_ids` | List all airline IDs | config |
| `get_airline_route_history` | Airline route history | supply |
| `get_airline_route_history_filtered` | Airline route history filtered | supply |
| `get_airline_routes` | Airline routes | supply |
| `get_arbitration_modes` | Arbitration modes | supply |
| `get_booking_log` | Booking log | demand |
| `get_budget_balance` | Get Budget Balance | pricing |
| `get_budget_levels` | Budget level types | pricing |
| `get_budget_user_balance` | User-level budget balance | pricing |
| `get_countries` | List all countries | config |
| `get_decompressed_object` | Decompress S3/stored object | config |
| `get_demand_experiment_contextid` | Experiment context ID | demand |
| `get_demand_experiment_variant` | Experiment variant namespace | demand |
| `get_fare_check_result` | Fare check result | supply |
| `get_feature_flags` | Get Feature Flags | config |
| `get_flag_applications` | List Flag Applications | config |
| `get_flag_configuration` | Get Flag Configuration Detail | config |
| `get_flight_info` | Booking flight info | demand |
| `get_flight_info_json` | Booking flight info (JSON) | demand |
| `get_inventory_detail` | Inventory detail | supply |
| `get_inventory_types` | Inventory types | supply |
| `get_promo_label_data` | Get Promo Label Supporting Data | demand |
| `get_promo_label_detail` | Get single promo label full config by promoLabelId | demand |
| `get_provider_source_histories` | Sourcing change history | supply, supply-search |
| `get_provider_source_latest_version` | Latest sourcing version | supply, supply-search |
| `get_provider_sourcing` | Provider sourcing config | supply, supply-search |
| `get_special_fare_config` | Special fare config | supply |
| `get_winner_details` | Winner details | demand |
| `list_active_budgets` | List active budgets | pricing |
| `list_mongo_collections` | List MongoDB Collections | demand |
| `load_autopilot_rules` | Load Autopilot Pricing Rules | pricing |
| `load_baseline_pricing_rules` | Base markup/margin rules | pricing |
| `load_bundling_pricing_rules` | Bundle pricing (flight+hotel) | pricing |
| `load_commission_incentive_profiles` | Commission profile list | pricing |
| `load_commission_incentive_rules` | Commission rates | pricing |
| `load_condition_groups` | Reusable filter condition groups | config, pricing |
| `load_fare_adjuster_by_airport_tax` | Fare adjuster by airport tax | pricing, supply |
| `load_fare_adjuster_by_base_fare` | Fare adjuster by base fare | pricing, supply |
| `load_issuance_fee_rules` | Ticket issuance fees | pricing |
| `load_price_cut_modifier_rules` | Load Price Cut / Promo Modifier Rules | pricing |
| `load_price_prediction_rules` | Load Price Prediction Rules | pricing |
| `load_pricing_profiles` | Pricing profile names | pricing |
| `load_profiling_config` | Profiling configuration | demand |
| `load_tiered_incentive_rules` | Volume-based incentive tiers | pricing |
| `load_trx_fee_rules` | Transaction/service fee | pricing |
| `read_pricing_provider` | Pricing provider config | pricing, supply |
| `revalidate_regular_fare` | Revalidate regular fare | supply |
| `revalidate_special_fare` | Revalidate special fare | supply |
| `revalidate_upsell_fare` | Revalidate upsell fare | supply |
| `search_cache_by_id` | Search Cache by Search ID | demand |
| `search_cache_content` | Search Fare Cache by Route | demand |
| `search_promo_labels` | Search/list promo label configs | demand |
| `search_regular_fare` | Search regular fares | supply, supply-search |
| `search_special_fare` | Special fare search | supply |
| `search_upsell_fare` | Upsell fare search | supply |
| `search_user_profile` | Search user profile | demand |
| `search_winner` | Search winners | demand |
| `simple_crud_query` | MongoDB CRUD Query | demand |
| `simulate_search` | Simulate full user search | demand, supply |
| `update_autopilot_rules` | Update autopilot pricing rules (create/modify rules with conditions and adjustme | pricing |

## Summary

- **Claimed:** 64/64
- **Unclaimed:** 0

- **config:** 9 ops
- **demand:** 17 ops
- **pricing:** 22 ops
- **supply:** 22 ops
- **supply-search:** 4 ops
