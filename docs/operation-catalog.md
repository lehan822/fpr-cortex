# Operation Catalog

> Auto-generated — do not edit manually.
> Run: `python scripts/generate-catalog.py`

**Total: 64 operations** across 1 backend(s): fprtool

| operationId | Description | Domain |
|---|---|---|
| `check_fare` | Check fare | supply |
| `check_tiered_incentive_progress` | Check Tiered Incentive Progress for a Booking | pricing |
| `convert_currency` | Convert Currency | config |
| `get_activity_log` | Get Activity/Audit Log | config |
| `get_airline_ids` | List All Airline IDs | config |
| `get_airline_route_history` | Get airline route history | supply |
| `get_airline_route_history_filtered` | Get airline route history filtered | ❌ unclaimed |
| `get_airline_routes` | Get airline routes | supply |
| `get_arbitration_modes` | Get arbitration modes | supply |
| `get_booking_log` | Get Booking Log | demand |
| `get_budget_balance` | Get Budget Balance | pricing |
| `get_budget_levels` | Get Budget Level Types | pricing |
| `get_budget_user_balance` | Get User-Level Budget Balance | pricing |
| `get_countries` | List All Countries | config |
| `get_decompressed_object` | Get decompressed object | ❌ unclaimed |
| `get_demand_experiment_contextid` | Experiment context ID | ❌ unclaimed |
| `get_demand_experiment_variant` | Experiment variant namespace | ❌ unclaimed |
| `get_fare_check_result` | Get fare check result | supply |
| `get_feature_flags` | Get Feature Flags | config |
| `get_flag_applications` | List Flag Applications | config |
| `get_flag_configuration` | Get Flag Configuration Detail | config |
| `get_flight_info` | Get Booking Flight Info | demand |
| `get_flight_info_json` | Get Booking Flight Info (JSON) | demand |
| `get_inventory_detail` | Get inventory detail | supply |
| `get_inventory_types` | Get inventory types | supply |
| `get_promo_label_data` | Get Promo Label Supporting Data | demand |
| `get_promo_label_detail` | Get single promo label by ID | ❌ unclaimed |
| `get_provider_source_histories` | Get provider source histories | supply-search |
| `get_provider_source_latest_version` | Get provider source latest version | supply-search |
| `get_provider_sourcing` | Get provider sourcing | supply, supply-search |
| `get_special_fare_config` | Get special fare config | supply |
| `get_winner_details` | Get Winner Details | demand |
| `list_active_budgets` | List Active Budgets | pricing |
| `list_mongo_collections` | List MongoDB Collections | demand |
| `load_autopilot_rules` | Load Autopilot Pricing Rules | pricing |
| `load_baseline_pricing_rules` | Load Baseline Pricing Rules | pricing |
| `load_bundling_pricing_rules` | Load Bundling Pricing Rules | pricing |
| `load_commission_incentive_profiles` | Load Commission Incentive Profiles | pricing |
| `load_commission_incentive_rules` | Load Commission Incentive Rules | pricing |
| `load_condition_groups` | Load Condition Groups | config |
| `load_fare_adjuster_by_airport_tax` | Load fare adjuster by airport tax | supply |
| `load_fare_adjuster_by_base_fare` | Load fare adjuster by base fare | supply |
| `load_issuance_fee_rules` | Load Ticket Issuance Fee Rules | pricing |
| `load_price_cut_modifier_rules` | Load Price Cut / Promo Modifier Rules | pricing |
| `load_price_prediction_rules` | Load Price Prediction Rules | pricing |
| `load_pricing_profiles` | Load Pricing Profile Names | pricing |
| `load_profiling_config` | Load Profiling Configuration | demand |
| `load_tiered_incentive_rules` | Load Tiered Incentive Rules | pricing |
| `load_trx_fee_rules` | Load Transaction Fee Rules | pricing |
| `read_pricing_provider` | Read pricing provider | supply |
| `revalidate_regular_fare` | Revalidate regular fare | ❌ unclaimed |
| `revalidate_special_fare` | Revalidate special fare | ❌ unclaimed |
| `revalidate_upsell_fare` | Revalidate upsell fare | ❌ unclaimed |
| `search_cache_by_id` | Search Cache by Search ID | demand |
| `search_cache_content` | Search Fare Cache by Route | demand |
| `search_promo_labels` | Search Promo Labels | demand |
| `search_regular_fare` | Search regular fare | supply, supply-search |
| `search_special_fare` | Special fare search | ❌ unclaimed |
| `search_upsell_fare` | Upsell fare search | ❌ unclaimed |
| `search_user_profile` | Search User Profile | demand |
| `search_winner` | Search Winners | demand |
| `simple_crud_query` | MongoDB CRUD Query | demand |
| `simulate_search` | Simulate Flight Search | demand |
| `update_autopilot_rules` | Update autopilot pricing rules (create/modify rules with conditions and adjustme | pricing |

## Summary

- **Claimed:** 54/64
- **Unclaimed:** 10

- **config:** 8 ops
- **demand:** 14 ops
- **pricing:** 17 ops
- **supply:** 13 ops
- **supply-search:** 4 ops
