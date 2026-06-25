# Operation Catalog

> Auto-generated — do not edit manually.
> Run: `python scripts/generate-catalog.py`

**Total: 73 operations** across 1 backend(s): fprtool

| operationId | Description | Domain |
|---|---|---|
| `check_fare` | Check fare validity | supply |
| `check_tiered_incentive_progress` | Check Tiered Incentive Progress for a Booking | pricing |
| `convert_currency` | Convert currency | sysinteg |
| `decrypt_flight_id` | Decrypt flight ID | 3ps-datainfo |
| `get_activity_log` | Get Activity/Audit Log | sysinteg |
| `get_airline_ids` | All airline IDs | 3ps-datainfo, sysinteg |
| `get_airline_route_history` | Route change history | 3ps-datainfo |
| `get_airline_route_history_filtered` | Filtered route history | 3ps-datainfo |
| `get_airline_routes` | All airline routes | 3ps-datainfo |
| `get_airport_list` | Airport info list | 3ps-datainfo |
| `get_arbitration_modes` | Arbitration modes | supply |
| `get_booking_log` | Booking event logs from S3 | demand |
| `get_budget_balance` | Get Budget Balance | pricing |
| `get_budget_levels` | Get Budget Level Types | pricing |
| `get_budget_user_balance` | Get User-Level Budget Balance | pricing |
| `get_countries` | All countries | 3ps-datainfo, sysinteg |
| `get_decompressed_object` | Decompress S3/stored object | sysinteg |
| `get_demand_experiment_contextid` | Experiment context ID | demand |
| `get_demand_experiment_variant` | Experiment variant namespace | demand |
| `get_enabled_provider` | Enabled providers list | supply |
| `get_fare_check_result` | Fare check result | supply |
| `get_feature_flags` | Get Feature Flags | sysinteg |
| `get_flag_applications` | List Flag Applications | sysinteg |
| `get_flag_configuration` | Get Flag Configuration Detail | sysinteg |
| `get_flight_info` | Booking details by ID | demand |
| `get_flight_info_json` | Booking JSON (full pricing debug) | demand |
| `get_inventory_detail` | Inventory detail | supply |
| `get_inventory_types` | Inventory types | supply |
| `get_promo_label_data` | Get Promo Label Supporting Data | ❌ unclaimed |
| `get_promo_label_detail` | Get single promo label full config | ❌ unclaimed |
| `get_provider_source_histories` | Sourcing change history | supply |
| `get_provider_source_latest_version` | Latest sourcing version | supply |
| `get_provider_sourcing` | Provider sourcing config | supply |
| `get_special_fare_config` | Special fare configuration | supply |
| `get_winner_details` | Winner (selected fare/provider) | ❌ unclaimed |
| `list_active_budgets` | List Active Budgets | pricing |
| `list_mongo_collections` | List MongoDB Collections | demand |
| `load_autopilot_rules` | Load Autopilot Pricing Rules | pricing |
| `load_baseline_pricing_rules` | Load Baseline Pricing Rules | pricing |
| `load_bundling_pricing_rules` | Load Bundling Pricing Rules | pricing |
| `load_commission_incentive_profiles` | Load Commission Incentive Profiles | pricing |
| `load_commission_incentive_rules` | Load Commission Incentive Rules | pricing |
| `load_condition_groups` | Load Condition Groups | sysinteg |
| `load_fare_adjuster_by_airport_tax` | Load fare adjuster by airport tax | ❌ unclaimed |
| `load_fare_adjuster_by_base_fare` | Load fare adjuster by base fare | ❌ unclaimed |
| `load_issuance_fee_rules` | Load Ticket Issuance Fee Rules | pricing |
| `load_price_cut_modifier_rules` | Load Price Cut / Promo Modifier Rules | pricing |
| `load_price_prediction_rules` | Load Price Prediction Rules | pricing |
| `load_pricing_profiles` | Load Pricing Profile Names | pricing |
| `load_profiling_config` | Profiling configuration | ❌ unclaimed |
| `load_tiered_incentive_rules` | Load Tiered Incentive Rules | pricing |
| `load_trx_fee_rules` | Load Transaction Fee Rules | pricing |
| `multi_country_crud` | Multi-country config CRUD | 3ps-datainfo |
| `pronto_get_list_destination` | List tags by destination | 3ps-datainfo |
| `pronto_get_list_tag_name` | List tags by name | 3ps-datainfo |
| `pronto_get_static_data` | Tagging static data | 3ps-datainfo |
| `pronto_view_destination` | View tag detail by destination | 3ps-datainfo |
| `pronto_view_tag_name` | View tag detail by name | 3ps-datainfo |
| `read_pricing_provider` | Read pricing provider | ❌ unclaimed |
| `revalidate_regular_fare` | Revalidate regular fare | supply |
| `revalidate_special_fare` | Revalidate special fare | supply |
| `revalidate_upsell_fare` | Revalidate upsell fare | supply |
| `search_cache_by_id` | Search Cache by Search ID | demand |
| `search_cache_content` | Search Fare Cache by Route | demand |
| `search_metadata` | EFS metadata by searchID | supply |
| `search_promo_labels` | Search/list promo labels | ❌ unclaimed |
| `search_regular_fare` | Search regular fares | supply |
| `search_special_fare` | Special fare search | supply |
| `search_upsell_fare` | Upsell fare search | supply |
| `search_user_profile` | Search user profile | ❌ unclaimed |
| `search_winner` | Search winners by route | supply |
| `simulate_search` | Simulate full user search | demand, supply |
| `update_autopilot_rules` | Update autopilot pricing rules (create/modify rules with conditions and adjustme | pricing |

## Summary

- **Claimed:** 64/73
- **Unclaimed:** 9

- **3ps-datainfo:** 13 ops
- **demand:** 9 ops
- **pricing:** 17 ops
- **supply:** 19 ops
- **sysinteg:** 9 ops
