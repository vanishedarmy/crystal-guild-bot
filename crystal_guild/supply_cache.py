"""Sealed seasonal supplies: one weighted reward per inventory cache."""

SPOOKY_CACHE_ID = "spooky_supply_cache"
SPOOKY_CACHE_TIERS = (
    ("common", 45, ("potion", "antidote", "eye_drops", "echo_herbs")),
    ("uncommon", 25, ("hi_potion", "ether", "phoenix_down", "tent")),
    ("rare", 10, ("x_potion", "hi_ether", "remedy")),
    ("artifact", 4, ("elixir",)),
    ("legendary", 1, ("megalixir",)),
    ("gil", 15, ()),
)
SPOOKY_CACHE_DESCRIPTION = (
    "A sealed cache. Open from the Seasonal tab or Inventory for one random reward: "
    "45% common, 25% uncommon, 10% rare, 4% artifact, 1% legendary item, "
    "or 15% chance of 100–750 Gil. Items within each rarity are equally likely. "
    "Consumes one cache; open outside adventures and combat, even after the event ends."
)


def roll_spooky_cache(rng):
    """Integer buckets keep the published percentages exact."""
    roll = rng.randrange(100)
    for rarity, weight, items in SPOOKY_CACHE_TIERS:
        if roll < weight:
            if rarity == "gil":
                return {"kind": "gil", "amount": rng.randint(100, 750)}
            return {"kind": "item", "rarity": rarity, "item_id": rng.choice(items), "quantity": 1}
        roll -= weight
    raise RuntimeError("Spooky cache weights must total 100")
