"""
Simulated outputs of 35 specialized analytics agents for a root-cause-analysis
query on L'Oréal Vietnam Q3 2025 revenue decline.

Each agent returns a small structured "dataframe" (list of uniform dicts).
This mirrors a realistic agentic RCA flow where each agent queries the data
warehouse for one specific slice, then the orchestrator hands all results
to a single Response Generation Agent for synthesis.

Story baked into the data (the "ground truth" root causes):

  1. NORTH VIETNAM STOCK-OUTS — Hanoi DC had a customs-clearance delay on
     imported DPD products in late August / early September. La Roche-Posay,
     CeraVe, SkinCeuticals affected. Logistics OTD and lead times spike.

  2. BEAUTY REPUBLIC COMPETITIVE OFFENSIVE — A fictional local competitor
     launched 4 LUXE-tier SKUs at 25–30% discounts on TikTok Shop. Impacts
     Lancôme, Kiehl's, YSL share, especially online.

  3. SAIGON DISTRIBUTION CO. INVENTORY CRISIS — Major distributor in HCMC
     had working-capital issues, cut inventory holdings from 28 to 11 days,
     reducing Modern Trade coverage in South Vietnam.

Some agents return "red herring" data (normal patterns) so the synthesis
task isn't trivially keyword-matchable.
"""

# ---------------------------------------------------------------------------
# Top-level context
# ---------------------------------------------------------------------------

DIAGNOSTIC_QUERY = (
    "L'Oréal Vietnam Q3 2025 net revenue dropped 18.4% versus Q2 2025 "
    "(85.4B VND → 69.7B VND, a decline of 15.7B VND). "
    "Identify the top 3 root causes of this decline, ranked by impact, "
    "with quantified evidence and concrete next actions."
)

CONTEXT = {
    "company": "L'Oréal Vietnam",
    "comparison_period": "Q3 2025 vs Q2 2025",
    "q2_revenue_vnd_b": 85.4,
    "q3_revenue_vnd_b": 69.7,
    "absolute_decline_vnd_b": -15.7,
    "decline_pct": -18.4,
    "agents_invoked": 35,
}

# ---------------------------------------------------------------------------
# Agent results
# Each entry: {name, description, data: list[dict]}
# ---------------------------------------------------------------------------

AGENTS = [
    # ----------------- Revenue decomposition (1–6) -----------------
    {
        "name": "revenue_by_brand_qoq",
        "description": "Q2 vs Q3 revenue by brand (VND billions) with % change.",
        "data": [
            {"brand": "La Roche-Posay", "q2_vnd_b": 12.5, "q3_vnd_b": 8.5, "change_pct": -32.0},
            {"brand": "CeraVe",          "q2_vnd_b":  8.2, "q3_vnd_b": 5.9, "change_pct": -28.0},
            {"brand": "SkinCeuticals",   "q2_vnd_b":  2.7, "q3_vnd_b": 2.1, "change_pct": -22.2},
            {"brand": "Vichy",           "q2_vnd_b":  4.0, "q3_vnd_b": 3.4, "change_pct": -15.0},
            {"brand": "Lancôme",         "q2_vnd_b": 12.0, "q3_vnd_b": 9.4, "change_pct": -21.7},
            {"brand": "Kiehl's",         "q2_vnd_b":  5.6, "q3_vnd_b": 4.5, "change_pct": -19.6},
            {"brand": "Yves Saint Laurent","q2_vnd_b": 6.6, "q3_vnd_b": 5.4, "change_pct": -18.2},
            {"brand": "Biotherm",        "q2_vnd_b":  0.8, "q3_vnd_b": 0.7, "change_pct": -12.5},
            {"brand": "L'Oréal Paris",   "q2_vnd_b": 10.0, "q3_vnd_b": 9.2, "change_pct":  -8.0},
            {"brand": "Maybelline New York","q2_vnd_b": 6.4,"q3_vnd_b": 6.1, "change_pct":  -4.7},
            {"brand": "Garnier",         "q2_vnd_b":  4.9, "q3_vnd_b": 4.7, "change_pct":  -4.1},
            {"brand": "NYX Professional Makeup","q2_vnd_b": 1.6,"q3_vnd_b": 1.5,"change_pct": -6.3},
            {"brand": "Essie",           "q2_vnd_b":  1.0, "q3_vnd_b": 0.9, "change_pct": -10.0},
            {"brand": "Kérastase",       "q2_vnd_b":  4.0, "q3_vnd_b": 3.8, "change_pct":  -5.0},
            {"brand": "L'Oréal Professionnel","q2_vnd_b": 5.1,"q3_vnd_b": 3.1,"change_pct":-39.2},
        ],
    },
    {
        "name": "revenue_by_division_qoq",
        "description": "Q2 vs Q3 revenue by division (CPD, LUXE, DPD, PPD).",
        "data": [
            {"division": "DPD",  "q2_vnd_b": 27.4, "q3_vnd_b": 20.2, "change_pct": -26.3},
            {"division": "LUXE", "q2_vnd_b": 25.0, "q3_vnd_b": 20.0, "change_pct": -20.0},
            {"division": "CPD",  "q2_vnd_b": 23.9, "q3_vnd_b": 22.4, "change_pct":  -6.3},
            {"division": "PPD",  "q2_vnd_b":  9.1, "q3_vnd_b":  7.1, "change_pct": -22.0},
        ],
    },
    {
        "name": "revenue_by_region_qoq",
        "description": "Q2 vs Q3 revenue by Vietnam region (North/Central/South).",
        "data": [
            {"region": "North (Hanoi + provinces)",   "q2_vnd_b": 28.5, "q3_vnd_b": 20.5, "change_pct": -28.1},
            {"region": "South (HCMC + Mekong Delta)", "q2_vnd_b": 42.1, "q3_vnd_b": 34.1, "change_pct": -19.0},
            {"region": "Central (Da Nang + provinces)","q2_vnd_b": 14.8,"q3_vnd_b": 15.1, "change_pct":   2.0},
        ],
    },
    {
        "name": "revenue_by_channel_qoq",
        "description": "Q2 vs Q3 revenue by sales channel.",
        "data": [
            {"channel": "Modern Trade",     "q2_vnd_b": 32.5, "q3_vnd_b": 25.4, "change_pct": -21.8},
            {"channel": "E-commerce",       "q2_vnd_b": 24.1, "q3_vnd_b": 19.5, "change_pct": -19.1},
            {"channel": "Department Store", "q2_vnd_b": 14.8, "q3_vnd_b": 12.6, "change_pct": -14.9},
            {"channel": "Traditional Trade","q2_vnd_b": 11.2, "q3_vnd_b":  9.9, "change_pct": -11.6},
            {"channel": "Direct (DTC)",     "q2_vnd_b":  2.8, "q3_vnd_b":  2.3, "change_pct": -17.9},
        ],
    },
    {
        "name": "top_declining_skus",
        "description": "Top 10 SKUs by absolute VND decline Q2→Q3.",
        "data": [
            {"sku_id": "LRP-EFFC-400",  "sku_name": "La Roche-Posay Effaclar Duo 400ml",   "decline_vnd_m": 1850.0, "decline_pct": -42.0},
            {"sku_id": "CRV-MOIST-454","sku_name": "CeraVe Moisturizing Cream 454g",        "decline_vnd_m": 1420.0, "decline_pct": -38.0},
            {"sku_id": "LAN-AGP-50",   "sku_name": "Lancôme Advanced Génifique 50ml",       "decline_vnd_m":  980.0, "decline_pct": -24.0},
            {"sku_id": "LRP-TOLER-40", "sku_name": "La Roche-Posay Toleriane Sensitive 40ml","decline_vnd_m": 870.0, "decline_pct": -35.0},
            {"sku_id": "KHL-MIDN-30",  "sku_name": "Kiehl's Midnight Recovery Serum 30ml",  "decline_vnd_m":  720.0, "decline_pct": -22.0},
            {"sku_id": "CRV-HYDR-355","sku_name": "CeraVe Hydrating Cleanser 355ml",        "decline_vnd_m":  680.0, "decline_pct": -31.0},
            {"sku_id": "SKC-CEF-30",  "sku_name": "SkinCeuticals C E Ferulic 30ml",         "decline_vnd_m":  610.0, "decline_pct": -28.0},
            {"sku_id": "YSL-LIP-208", "sku_name": "YSL Rouge Pur Couture Lipstick",         "decline_vnd_m":  580.0, "decline_pct": -19.0},
            {"sku_id": "LOP-AGEPR-50","sku_name": "L'Oréal Paris Age Perfect 50ml",         "decline_vnd_m":  410.0, "decline_pct":  -9.0},
            {"sku_id": "LAN-RENERG-50","sku_name": "Lancôme Rénergie HCF Triple 50ml",      "decline_vnd_m":  390.0, "decline_pct": -21.0},
        ],
    },
    {
        "name": "top_declining_stores",
        "description": "Top 8 individual stores by absolute Q3 revenue decline.",
        "data": [
            {"store_id": "MT-HN-VINHOMES-001","store": "Vinhomes Times City (MT)","city": "Hanoi",  "decline_vnd_m": 980.0, "decline_pct": -34.0},
            {"store_id": "MT-HN-LOTTE-014",  "store": "Lotte Mall West Lake (MT)","city": "Hanoi",  "decline_vnd_m": 740.0, "decline_pct": -29.0},
            {"store_id": "MT-HCM-AEON-022",  "store": "AEON Tan Phu (MT)",      "city": "HCMC",   "decline_vnd_m": 680.0, "decline_pct": -25.0},
            {"store_id": "MT-HCM-CRESC-018", "store": "Crescent Mall D7 (MT)",  "city": "HCMC",   "decline_vnd_m": 610.0, "decline_pct": -22.0},
            {"store_id": "DS-HCM-PARKS-007", "store": "Parkson Saigon (DS)",    "city": "HCMC",   "decline_vnd_m": 520.0, "decline_pct": -23.0},
            {"store_id": "MT-HCM-BIGC-031",  "store": "Big C An Phú (MT)",      "city": "HCMC",   "decline_vnd_m": 480.0, "decline_pct": -19.0},
            {"store_id": "MT-CT-VIN-009",    "store": "Vincom Plaza Cần Thơ (MT)","city":"Can Tho","decline_vnd_m": 320.0, "decline_pct": -27.0},
            {"store_id": "MT-DN-LOTTE-003",  "store": "Lotte Mart Đà Nẵng (MT)","city": "Da Nang", "decline_vnd_m":  90.0, "decline_pct":  -4.0},
        ],
    },

    # ----------------- Supply chain / inventory (7–14) -----------------
    {
        "name": "warehouse_oos_days",
        "description": "Out-of-stock days per warehouse in Q3 (target: <5 days).",
        "data": [
            {"warehouse": "Hanoi DC (North)",   "oos_days_q2": 3.2, "oos_days_q3": 21.4, "delta": 18.2},
            {"warehouse": "HCMC DC (South)",    "oos_days_q2": 2.8, "oos_days_q3":  6.1, "delta":  3.3},
            {"warehouse": "Da Nang DC (Central)","oos_days_q2": 1.9,"oos_days_q3":  2.4, "delta":  0.5},
            {"warehouse": "Bình Dương Hub",     "oos_days_q2": 2.1, "oos_days_q3":  3.0, "delta":  0.9},
        ],
    },
    {
        "name": "stockout_events_by_brand",
        "description": "Stock-out incidents per brand in Q3, with primary warehouse.",
        "data": [
            {"brand": "La Roche-Posay","incidents_q3": 47,"primary_warehouse": "Hanoi DC","longest_oos_days": 14},
            {"brand": "CeraVe",        "incidents_q3": 38,"primary_warehouse": "Hanoi DC","longest_oos_days": 12},
            {"brand": "SkinCeuticals", "incidents_q3": 22,"primary_warehouse": "Hanoi DC","longest_oos_days":  9},
            {"brand": "Vichy",         "incidents_q3": 11,"primary_warehouse": "Hanoi DC","longest_oos_days":  5},
            {"brand": "Lancôme",       "incidents_q3":  4,"primary_warehouse": "HCMC DC", "longest_oos_days":  2},
            {"brand": "L'Oréal Paris", "incidents_q3":  3,"primary_warehouse": "HCMC DC", "longest_oos_days":  1},
            {"brand": "Maybelline",    "incidents_q3":  2,"primary_warehouse": "HCMC DC", "longest_oos_days":  1},
        ],
    },
    {
        "name": "logistics_on_time_delivery",
        "description": "On-time delivery % by inbound route, Q2 vs Q3.",
        "data": [
            {"route": "Port HCMC → Hanoi DC", "otd_q2_pct": 94.0, "otd_q3_pct": 71.0, "delta_pct": -23.0},
            {"route": "Port HCMC → HCMC DC",  "otd_q2_pct": 96.0, "otd_q3_pct": 93.0, "delta_pct":  -3.0},
            {"route": "Port HCMC → Da Nang",  "otd_q2_pct": 92.0, "otd_q3_pct": 91.0, "delta_pct":  -1.0},
            {"route": "Air Freight Express",  "otd_q2_pct": 98.0, "otd_q3_pct": 97.0, "delta_pct":  -1.0},
        ],
    },
    {
        "name": "customs_clearance_lead_times",
        "description": "Customs clearance lead time (days) by month for imported DPD products.",
        "data": [
            {"month": "2025-04", "avg_clearance_days": 4.1, "max_clearance_days":  6, "shipments": 28},
            {"month": "2025-05", "avg_clearance_days": 4.3, "max_clearance_days":  7, "shipments": 31},
            {"month": "2025-06", "avg_clearance_days": 4.0, "max_clearance_days":  6, "shipments": 30},
            {"month": "2025-07", "avg_clearance_days": 4.5, "max_clearance_days":  8, "shipments": 29},
            {"month": "2025-08", "avg_clearance_days": 11.8,"max_clearance_days": 22, "shipments": 27},
            {"month": "2025-09", "avg_clearance_days": 18.2,"max_clearance_days": 31, "shipments": 24},
        ],
    },
    {
        "name": "forecast_accuracy_by_division",
        "description": "Demand forecast accuracy (MAPE-based) by division, Q2 vs Q3.",
        "data": [
            {"division": "DPD", "accuracy_q2_pct": 87.0, "accuracy_q3_pct": 62.0, "delta_pct": -25.0},
            {"division": "LUXE","accuracy_q2_pct": 84.0, "accuracy_q3_pct": 79.0, "delta_pct":  -5.0},
            {"division": "CPD", "accuracy_q2_pct": 89.0, "accuracy_q3_pct": 87.0, "delta_pct":  -2.0},
            {"division": "PPD", "accuracy_q2_pct": 82.0, "accuracy_q3_pct": 81.0, "delta_pct":  -1.0},
        ],
    },
    {
        "name": "inventory_turnover",
        "description": "Inventory turnover ratio by warehouse, Q3 (higher = stock missing/depleted).",
        "data": [
            {"warehouse": "Hanoi DC",    "turnover_q2": 4.2, "turnover_q3": 8.9, "interpretation": "Stock depleted"},
            {"warehouse": "HCMC DC",     "turnover_q2": 4.5, "turnover_q3": 5.1, "interpretation": "Normal"},
            {"warehouse": "Da Nang DC",  "turnover_q2": 3.9, "turnover_q3": 4.0, "interpretation": "Normal"},
            {"warehouse": "Bình Dương Hub","turnover_q2":4.3,"turnover_q3": 4.4, "interpretation": "Normal"},
        ],
    },
    {
        "name": "raw_material_cost_trends",
        "description": "Key raw material cost index trends (base = 100 at Q1 2025).",
        "data": [
            {"material": "Glycerin",         "q1_index": 100.0, "q2_index": 101.2, "q3_index": 102.4},
            {"material": "Hyaluronic Acid",  "q1_index": 100.0, "q2_index":  98.7, "q3_index":  99.1},
            {"material": "Niacinamide",      "q1_index": 100.0, "q2_index":  99.4, "q3_index":  98.8},
            {"material": "Packaging (glass)","q1_index": 100.0, "q2_index": 103.1, "q3_index": 104.0},
        ],
    },
    {
        "name": "import_tariff_changes",
        "description": "Tariff changes affecting L'Oréal imports in Q3.",
        "data": [
            {"product_category": "Skincare", "hs_code": "3304.99","tariff_q2_pct": 10.0, "tariff_q3_pct": 10.0, "change": "No change"},
            {"product_category": "Makeup",   "hs_code": "3304.10","tariff_q2_pct": 12.0, "tariff_q3_pct": 12.0, "change": "No change"},
            {"product_category": "Haircare", "hs_code": "3305.90","tariff_q2_pct":  8.0, "tariff_q3_pct":  8.0, "change": "No change"},
        ],
    },

    # ----------------- Distributor & trade (15–18) -----------------
    {
        "name": "distributor_performance_scores",
        "description": "Distributor scorecard (0–10 scale) Q2 vs Q3.",
        "data": [
            {"distributor": "Saigon Distribution Co.",    "region": "South",  "score_q2": 8.2, "score_q3": 4.1, "delta": -4.1},
            {"distributor": "Hanoi Trading Group",        "region": "North",  "score_q2": 7.8, "score_q3": 7.4, "delta": -0.4},
            {"distributor": "Mekong Beauty Partners",     "region": "South",  "score_q2": 7.5, "score_q3": 7.6, "delta":  0.1},
            {"distributor": "Central Vietnam Distribution","region":"Central","score_q2": 7.1, "score_q3": 7.3, "delta":  0.2},
            {"distributor": "Northern Highland Trading",  "region": "North",  "score_q2": 6.9, "score_q3": 6.7, "delta": -0.2},
        ],
    },
    {
        "name": "distributor_inventory_days",
        "description": "Inventory days held by each distributor (target: 21–28).",
        "data": [
            {"distributor": "Saigon Distribution Co.",   "inv_days_q2": 28.0, "inv_days_q3": 11.0, "note": "Below safety threshold"},
            {"distributor": "Hanoi Trading Group",       "inv_days_q2": 24.0, "inv_days_q3": 22.0, "note": "Normal"},
            {"distributor": "Mekong Beauty Partners",    "inv_days_q2": 26.0, "inv_days_q3": 25.0, "note": "Normal"},
            {"distributor": "Central Vietnam Distribution","inv_days_q2":22.0,"inv_days_q3": 23.0, "note": "Normal"},
            {"distributor": "Northern Highland Trading", "inv_days_q2": 25.0, "inv_days_q3": 24.0, "note": "Normal"},
        ],
    },
    {
        "name": "distributor_margin_changes",
        "description": "Distributor margin % changes Q2→Q3 (red herring; mostly flat).",
        "data": [
            {"distributor": "Saigon Distribution Co.",   "margin_q2_pct": 18.0, "margin_q3_pct": 18.0},
            {"distributor": "Hanoi Trading Group",       "margin_q2_pct": 17.5, "margin_q3_pct": 17.5},
            {"distributor": "Mekong Beauty Partners",    "margin_q2_pct": 18.5, "margin_q3_pct": 18.5},
            {"distributor": "Central Vietnam Distribution","margin_q2_pct":17.0,"margin_q3_pct": 17.0},
            {"distributor": "Northern Highland Trading", "margin_q2_pct": 17.8, "margin_q3_pct": 17.8},
        ],
    },
    {
        "name": "sales_force_coverage",
        "description": "Field sales rep headcount by region.",
        "data": [
            {"region": "HCMC",     "reps_q2": 42, "reps_q3": 39, "delta": -3, "note": "3 attritions not yet backfilled"},
            {"region": "Hanoi",    "reps_q2": 35, "reps_q3": 35, "delta":  0, "note": "Stable"},
            {"region": "Da Nang",  "reps_q2": 12, "reps_q3": 12, "delta":  0, "note": "Stable"},
            {"region": "Mekong",   "reps_q2": 18, "reps_q3": 18, "delta":  0, "note": "Stable"},
        ],
    },

    # ----------------- Competitive & market (19–23) -----------------
    {
        "name": "competitor_price_changes",
        "description": "Notable competitor price moves in Q3.",
        "data": [
            {"competitor": "Beauty Republic","tier": "LUXE","action": "Aggressive discount",   "discount_pct": -28.0,"channel": "TikTok Shop","duration_weeks": 8},
            {"competitor": "Beauty Republic","tier": "LUXE","action": "Bundle promo",          "discount_pct": -22.0,"channel": "Shopee",     "duration_weeks": 6},
            {"competitor": "Innisfree",     "tier": "Mass","action": "EOSS",                   "discount_pct": -15.0,"channel": "Multi",      "duration_weeks": 3},
            {"competitor": "The Ordinary",  "tier": "Dermo","action": "Direct entry pricing", "discount_pct":   0.0,"channel": "Shopee",     "duration_weeks": 12},
            {"competitor": "Hada Labo",     "tier": "Dermo","action": "Standard promo",       "discount_pct":  -8.0,"channel": "Modern Trade","duration_weeks": 4},
        ],
    },
    {
        "name": "competitor_new_launches",
        "description": "New competitor SKUs launched in Q3 targeting our segments.",
        "data": [
            {"competitor": "Beauty Republic","sku": "BR Aurora Serum 30ml",  "target_segment": "LUXE Anti-aging", "launch_channel": "TikTok Shop","launch_marketing_buzz": "High"},
            {"competitor": "Beauty Republic","sku": "BR Crystal Cream 50ml", "target_segment": "LUXE Moisturizer","launch_channel": "TikTok Shop","launch_marketing_buzz": "High"},
            {"competitor": "Beauty Republic","sku": "BR Velvet Lipstick",    "target_segment": "LUXE Makeup",     "launch_channel": "TikTok Shop","launch_marketing_buzz": "High"},
            {"competitor": "Beauty Republic","sku": "BR Glow Tonic 200ml",   "target_segment": "LUXE Skincare",   "launch_channel": "TikTok Shop","launch_marketing_buzz": "Medium"},
            {"competitor": "Innisfree",     "sku": "Green Tea Foam Cleanser","target_segment": "Mass Cleansing", "launch_channel": "Multi",       "launch_marketing_buzz": "Low"},
        ],
    },
    {
        "name": "market_share_by_division",
        "description": "L'Oréal market share % by division (Nielsen ScanTrack).",
        "data": [
            {"division": "LUXE", "share_q2_pct": 32.4, "share_q3_pct": 28.1, "delta_pct": -4.3},
            {"division": "DPD",  "share_q2_pct": 26.8, "share_q3_pct": 22.5, "delta_pct": -4.3},
            {"division": "CPD",  "share_q2_pct": 18.4, "share_q3_pct": 18.0, "delta_pct": -0.4},
            {"division": "PPD",  "share_q2_pct": 41.2, "share_q3_pct": 40.8, "delta_pct": -0.4},
        ],
    },
    {
        "name": "category_market_growth",
        "description": "Total category growth (the cake is growing/shrinking).",
        "data": [
            {"category": "Skincare",  "market_growth_q3_yoy_pct":  6.2, "loreal_growth_q3_yoy_pct": -14.0},
            {"category": "Makeup",    "market_growth_q3_yoy_pct":  3.8, "loreal_growth_q3_yoy_pct":  -4.2},
            {"category": "Haircare",  "market_growth_q3_yoy_pct":  2.4, "loreal_growth_q3_yoy_pct":  -3.1},
            {"category": "Fragrance", "market_growth_q3_yoy_pct":  4.1, "loreal_growth_q3_yoy_pct":   1.8},
        ],
    },
    {
        "name": "ecom_traffic_trends",
        "description": "E-commerce traffic % change Q3 vs Q2 by platform and division.",
        "data": [
            {"platform": "TikTok Shop","division": "LUXE",     "traffic_change_pct": -35.0, "note": "Significant share loss"},
            {"platform": "TikTok Shop","division": "DPD",      "traffic_change_pct":  -8.0, "note": "Mild dip"},
            {"platform": "TikTok Shop","division": "CPD",      "traffic_change_pct":  -2.0, "note": "Normal"},
            {"platform": "Shopee",     "division": "LUXE",     "traffic_change_pct": -12.0, "note": "Share loss"},
            {"platform": "Shopee",     "division": "DPD",      "traffic_change_pct":  -6.0, "note": "Mild dip"},
            {"platform": "Shopee",     "division": "CPD",      "traffic_change_pct":   1.0, "note": "Normal"},
            {"platform": "Lazada",     "division": "All",      "traffic_change_pct":  -3.0, "note": "Normal"},
        ],
    },

    # ----------------- Marketing & customer (24–29) -----------------
    {
        "name": "marketing_spend_by_channel",
        "description": "Marketing spend (VND M) by channel Q2 vs Q3.",
        "data": [
            {"channel": "TikTok Ads",     "spend_q2_vnd_m": 2400, "spend_q3_vnd_m": 1900, "change_pct": -20.8},
            {"channel": "Meta Ads",       "spend_q2_vnd_m": 1800, "spend_q3_vnd_m": 1750, "change_pct":  -2.8},
            {"channel": "Google Ads",     "spend_q2_vnd_m": 1100, "spend_q3_vnd_m": 1050, "change_pct":  -4.5},
            {"channel": "KOL/Influencer", "spend_q2_vnd_m": 1600, "spend_q3_vnd_m": 1500, "change_pct":  -6.3},
            {"channel": "Offline OOH",    "spend_q2_vnd_m":  800, "spend_q3_vnd_m":  820, "change_pct":   2.5},
        ],
    },
    {
        "name": "promo_campaigns_active",
        "description": "L'Oréal-led promo campaigns running in Q3 (own promos, not competitor).",
        "data": [
            {"campaign": "Lancôme Loyalty Refill","tier": "LUXE","discount_pct": -15.0,"channel": "DTC + Counter","weeks_active": 12,"roi_index": 1.4},
            {"campaign": "CeraVe Back-to-School","tier": "DPD","discount_pct": -20.0,"channel": "E-com","weeks_active": 6,"roi_index": 0.9},
            {"campaign": "L'Oréal Paris Mass Promo","tier": "Mass","discount_pct": -10.0,"channel": "MT + E-com","weeks_active": 8,"roi_index": 1.8},
            {"campaign": "Maybelline TikTok Live", "tier": "Mass","discount_pct":  -8.0,"channel": "TikTok Shop","weeks_active": 4,"roi_index": 2.1},
        ],
    },
    {
        "name": "customer_returns",
        "description": "Customer return rate % by division (red herring; quality not the issue).",
        "data": [
            {"division": "LUXE", "return_rate_q2_pct": 1.8, "return_rate_q3_pct": 1.9, "delta_pct": 0.1},
            {"division": "DPD",  "return_rate_q2_pct": 2.1, "return_rate_q3_pct": 2.0, "delta_pct": -0.1},
            {"division": "CPD",  "return_rate_q2_pct": 1.4, "return_rate_q3_pct": 1.5, "delta_pct": 0.1},
            {"division": "PPD",  "return_rate_q2_pct": 1.2, "return_rate_q3_pct": 1.2, "delta_pct": 0.0},
        ],
    },
    {
        "name": "customer_complaint_volume",
        "description": "Customer complaint tickets by category Q2 vs Q3.",
        "data": [
            {"category": "Quality issues",        "tickets_q2": 124, "tickets_q3": 131, "change_pct":   5.6},
            {"category": "Delivery delays",       "tickets_q2":  87, "tickets_q3": 312, "change_pct": 258.6},
            {"category": "Stock unavailable",     "tickets_q2":  45, "tickets_q3": 287, "change_pct": 537.8},
            {"category": "Pricing complaints",    "tickets_q2":  62, "tickets_q3":  74, "change_pct":  19.4},
            {"category": "Counter staff issues",  "tickets_q2":  38, "tickets_q3":  41, "change_pct":   7.9},
        ],
    },
    {
        "name": "ecom_conversion_rates",
        "description": "E-commerce conversion rate % (rules out UX issues).",
        "data": [
            {"platform": "TikTok Shop","conv_q2_pct": 3.1, "conv_q3_pct": 3.0, "delta_pct": -0.1},
            {"platform": "Shopee",     "conv_q2_pct": 2.8, "conv_q3_pct": 2.7, "delta_pct": -0.1},
            {"platform": "Lazada",     "conv_q2_pct": 2.4, "conv_q3_pct": 2.5, "delta_pct":  0.1},
            {"platform": "DTC Site",   "conv_q2_pct": 4.2, "conv_q3_pct": 4.1, "delta_pct": -0.1},
        ],
    },
    {
        "name": "loyalty_program_engagement",
        "description": "Loyalty program active member counts and avg basket.",
        "data": [
            {"tier": "Diamond", "active_q2": 4200, "active_q3": 4150, "avg_basket_q2_vnd_k": 2400, "avg_basket_q3_vnd_k": 2350},
            {"tier": "Gold",    "active_q2": 18500,"active_q3": 18200,"avg_basket_q2_vnd_k": 1100, "avg_basket_q3_vnd_k": 1090},
            {"tier": "Silver",  "active_q2": 62000,"active_q3": 61400,"avg_basket_q2_vnd_k":  580, "avg_basket_q3_vnd_k":  570},
        ],
    },

    # ----------------- Macro / environmental (30–35) -----------------
    {
        "name": "fx_impact_vnd_usd",
        "description": "VND/USD exchange rate quarterly average and impact estimate.",
        "data": [
            {"period": "Q2 2025", "vnd_per_usd": 24850.0, "impact_estimate_vnd_b": 0.0},
            {"period": "Q3 2025", "vnd_per_usd": 25150.0, "impact_estimate_vnd_b": -0.3},
        ],
    },
    {
        "name": "weather_anomalies",
        "description": "Notable weather events vs typical Q3 monsoon patterns.",
        "data": [
            {"region": "North", "event": "Typhoon Yagi remnants",   "severity": "Moderate","traffic_impact_pct": -8.0,"duration_days": 4},
            {"region": "South", "event": "Normal monsoon",          "severity": "Low",     "traffic_impact_pct": -1.0,"duration_days": 0},
            {"region": "Central","event": "Brief flooding Hue",     "severity": "Low",     "traffic_impact_pct": -2.0,"duration_days": 2},
        ],
    },
    {
        "name": "holiday_calendar_impact",
        "description": "Major retail holidays in Q3 vs Q2 (normalized comparison).",
        "data": [
            {"period": "Q2", "key_holiday": "Reunification Day + Labor Day",   "shopping_uplift_pct": 8.0},
            {"period": "Q3", "key_holiday": "Mid-Autumn Festival",             "shopping_uplift_pct": 6.5},
            {"period": "Q3", "key_holiday": "Vietnam National Day (Sep 2)",    "shopping_uplift_pct": 4.0},
        ],
    },
    {
        "name": "new_store_openings",
        "description": "New store openings in Q3 (contributes positively).",
        "data": [
            {"store": "Vincom Mega Mall Smart City","city": "Hanoi", "open_date": "2025-08-15","expected_q3_revenue_vnd_m": 320.0},
            {"store": "Aeon Long Bien Phase 2",     "city": "Hanoi", "open_date": "2025-09-01","expected_q3_revenue_vnd_m": 240.0},
        ],
    },
    {
        "name": "store_closures",
        "description": "Store closures in Q3.",
        "data": [
            {"store": "Indochina Riverside Da Nang", "city": "Da Nang","close_date": "2025-07-20","q2_revenue_vnd_m": 180.0, "reason": "Mall renovation"},
        ],
    },
    {
        "name": "product_launches",
        "description": "L'Oréal product launches in Q3 (limited rollout).",
        "data": [
            {"sku": "Lancôme Idôle L'Intense EDP", "brand": "Lancôme",      "launch_date": "2025-08-10","planned_q3_revenue_vnd_m": 380.0, "actual_q3_revenue_vnd_m": 310.0},
            {"sku": "L'Oréal Paris Revitalift Filler","brand": "L'Oréal Paris","launch_date": "2025-09-05","planned_q3_revenue_vnd_m": 240.0,"actual_q3_revenue_vnd_m": 110.0},
        ],
    },
]


def get_full_payload() -> dict:
    """Return everything bundled for serialization."""
    return {
        "context": CONTEXT,
        "diagnostic_query": DIAGNOSTIC_QUERY,
        "agent_results": {a["name"]: a["data"] for a in AGENTS},
        "agent_descriptions": {a["name"]: a["description"] for a in AGENTS},
    }
