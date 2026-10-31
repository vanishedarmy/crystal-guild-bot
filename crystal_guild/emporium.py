"""Regional Moogle counters. Guild construction improves service, never stock access."""

STAPLES = ("potion", "antidote", "echo_herbs", "trail_rations")
REGIONAL_SHOPS = {
    'greenwind_plains': (18, 1, 9, 'Trailside Counter', 'Starter supplies and first equipment', ('eye_drops',)),
    'whispering_caverns': (18, 10, 19, 'Lantern Counter', 'Cavern recovery and status cures', ('ether', 'tent', 'phoenix_down')),
    'sable_coast': (18, 20, 29, 'Harbor Counter', 'Coastal elemental supplies', ('arctic_wind', 'lightning_marble', 'water_gem')),
    'magitek_wastes': (18, 30, 39, "Salvager's Counter", 'Salvaged battle gear and field support', ('warriors_tonic', 'war_horn', 'earth_drum')),
    'crystal_expanse': (18, 40, 49, 'Crystal Counter', 'Crystal weapons and Relic foundation supplies', ('x_potion', 'hi_ether', 'mages_incense')),
    'riftlands': (18, 50, 59, "Wayfarer's Counter", 'Rift survival supplies and intermediate gear', ('remedy', 'regen_tonic', 'smoke_bomb')),
    'shattered_frontier': (18, 60, 69, 'Frontier Outpost', 'Relic-awakening field supplies and balanced gear', ('remedy', 'hi_ether', 'regen_tonic')),
    'interdimensional_rift': (18, 70, 79, 'Astral Counter', 'Dimensional exploration gear and support', ('x_potion', 'hi_ether', 'mages_incense')),
    'omega_ruins': (18, 80, 89, 'Last Light Counter', 'High-level combat supplies', ('x_potion', 'remedy', 'phoenix_down')),
    'astral_threshold': (18, 90, 98, 'Starwatch Outpost', 'Elite supplies and veteran gear', ('x_potion', 'hi_ether', 'remedy')),
    'eclipsed_singularity_citadel': (18, 99, 99, 'Eclipse Refuge', 'Capstone provisions; specialized equipment remains exclusive', ('x_potion', 'remedy', 'phoenix_down')),
}


def shop_context(player, regions):
    region_id = str(player["current_region"] or "greenwind_plains")
    region = regions.get(region_id)
    if region_id not in REGIONAL_SHOPS or not region or int(player["level"]) < int(region.get("min_level", 1)):
        region_id = "greenwind_plains"
        region = regions[region_id]
    slots, floor, ceiling, name, specialty, supplies = REGIONAL_SHOPS[region_id]
    return {"id": region_id, "region_name": region["name"], "name": name,
            "specialty": specialty, "stock_slots": slots, "gear_floor": floor,
            "stock_level_cap": ceiling, "featured_supplies": supplies}


def eligible_stock(player, items, context):
    level = min(int(player["level"]), context["stock_level_cap"])
    job = str(player["current_job"])
    eligible = []
    for item in items.values():
        item_level = max(int(item.get("shop_level", 1)), int(item.get("min_level", 1)))
        if not item.get("shop") or item_level > level:
            continue
        # Relic/unique/crafting-only equipment must NEVER become purchasable,
        # regardless of malformed source flags or a previous cached rotation.
        if item.get("relic_id") or item.get("unsellable") or (
            item["type"] in {"weapon", "armor"}
            and str(item.get("rarity", "common")).lower() in {"relic", "artifact", "legendary"}
        ):
            continue
        if item.get("allowed_jobs") and job not in item["allowed_jobs"]:
            continue
        if job == "adventurer" and (item["type"] not in {"consumable", "accessory"} or item.get("allowed_jobs")):
            continue
        if item["type"] in {"weapon", "armor"} and item_level < context["gear_floor"]:
            continue
        eligible.append(item)
    return eligible


def guild_commerce(tiers):
    annex = int(tiers.get("emporium_annex", 0)) >= 1
    market = int(tiers.get("trading_post", 0)) >= 1
    quartermaster = max(0, min(5, int(tiers.get("quartermaster", 0))))
    return {"purchase_discount": 0.10 if annex else 0.0,
            "refresh_reduction": quartermaster * 0.03,
            "listing_fee_rate": 0.01 if market else 0.02,
            "sale_tax_rate": 0.03 if market else 0.05,
            "active_limit": 10 if market else 6,
            "annex_built": annex, "trading_post_built": market}


def purchase_price(item, perks):
    base = max(0, int(item.get("price", 0)))
    # Integer rounding keeps display, chat and Portal purchases identical.
    return max(1, base * (90 if perks["annex_built"] else 100) // 100) if base else 0
