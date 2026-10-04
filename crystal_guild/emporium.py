"""Regional Moogle counters. Guild construction improves service, never stock access."""

STAPLES = ("potion", "antidote", "echo_herbs", "trail_rations")
REGIONAL_SHOPS = {
    "greenwind_plains": (12, 1, 7, "Trailside Counter", "Travel supplies and starter gear", ("eye_drops",)),
    "whispering_caverns": (14, 5, 15, "Lantern Counter", "Recovery supplies for the caverns", ("ether", "tent", "phoenix_down")),
    "sable_coast": (16, 12, 27, "Harbor Counter", "Coastal gear and elemental supplies", ("arctic_wind", "lightning_marble", "water_gem")),
    "magitek_wastes": (18, 20, 41, "Salvager's Counter", "Battle gear and field support", ("warriors_tonic", "war_horn", "earth_drum")),
    "crystal_expanse": (18, 30, 54, "Crystal Counter", "Crystal gear and powerful recovery", ("x_potion", "hi_ether", "mages_incense")),
    "riftlands": (18, 40, 69, "Wayfarer's Counter", "Survival equipment and status recovery", ("remedy", "regen_tonic", "smoke_bomb")),
    "interdimensional_rift": (18, 50, 81, "Astral Counter", "Veteran gear and magical support", ("x_potion", "hi_ether", "mages_incense")),
    "omega_ruins": (18, 55, 99, "Last Light Counter", "Endgame field supplies and veteran gear", ("x_potion", "remedy", "phoenix_down")),
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
