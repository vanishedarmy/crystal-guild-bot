from __future__ import annotations

WORLD_EVENT_LEVEL_CAP_ABOVE_HIGHEST = 10
WORLD_EVENT_INITIAL_GRACE_SECONDS = 15 * 60
WORLD_EVENT_CHECK_MIN_SECONDS = 8 * 60
WORLD_EVENT_CHECK_MAX_SECONDS = 12 * 60
WORLD_EVENT_SPAWN_CHANCE = 0.25
WORLD_EVENT_POST_COOLDOWN_MIN_SECONDS = 30 * 60
WORLD_EVENT_POST_COOLDOWN_MAX_SECONDS = 45 * 60
WORLD_EVENT_RALLY_SECONDS = 90

WORLD_EVENTS = (
    {
        "id": "notorious_behemoth", "name": "Notorious Behemoth", "base_monster_id": "behemoth",
        "description": "A brutal apex monster known for overwhelming force.", "threat": "Extreme",
        "bonus_min": 6, "bonus_max": 10, "hp_mult": 1.35, "power_mult": 1.10, "reward_mult": 1.45,
        "art": "/world-events/a1/notorious_behemoth.webp",
    },
    {
        "id": "tainted_malboro", "name": "Tainted Malboro", "base_monster_id": "malboro",
        "description": "A corrupted horror that inflicts crippling afflictions.", "threat": "Severe",
        "bonus_min": 5, "bonus_max": 9, "hp_mult": 1.25, "power_mult": 1.08, "reward_mult": 1.40,
        "art": "/world-events/a1/tainted_malboro.webp",
    },
    {
        "id": "dark_iron_giant", "name": "Dark Iron Giant", "base_monster_id": "iron_giant",
        "description": "An immense armored executioner wreathed in menace.", "threat": "Extreme",
        "bonus_min": 6, "bonus_max": 10, "hp_mult": 1.40, "power_mult": 1.08, "reward_mult": 1.45,
        "art": "/world-events/a1/dark_iron_giant.webp",
    },
    {
        "id": "elder_adamantoise", "name": "Elder Adamantoise", "base_monster_id": "adamantoise",
        "description": "An ancient titan whose shell turns aside all but the strongest blows.", "threat": "Severe",
        "bonus_min": 4, "bonus_max": 8, "hp_mult": 1.55, "power_mult": 1.02, "reward_mult": 1.35,
        "art": "/world-events/a1/elder_adamantoise.webp",
    },
    {
        "id": "cursed_tonberry_king", "name": "Cursed Tonberry King", "base_monster_id": "tonberry_king",
        "description": "A slow, silent menace whose patience is deadlier than rage.", "threat": "Extreme",
        "bonus_min": 7, "bonus_max": 10, "hp_mult": 1.20, "power_mult": 1.14, "reward_mult": 1.50,
        "art": "/world-events/a1/cursed_tonberry_king.webp",
    },
    {
        "id": "savage_coeurl", "name": "Savage Coeurl", "base_monster_id": "coeurl",
        "description": "A lightning-fast predator that strikes before most can react.", "threat": "Dangerous",
        "bonus_min": 3, "bonus_max": 7, "hp_mult": 1.15, "power_mult": 1.08, "reward_mult": 1.30,
        "art": "/world-events/a1/savage_coeurl.webp",
    },
    {
        "id": "dread_bomb_king", "name": "Dread Bomb King", "base_monster_id": "bomb",
        "description": "A volatile terror that threatens devastation if left unchecked.", "threat": "Severe",
        "bonus_min": 4, "bonus_max": 8, "hp_mult": 1.18, "power_mult": 1.12, "reward_mult": 1.35,
        "art": "/world-events/a1/dread_bomb_king.webp",
    },
    {
        "id": "twisted_ahriman", "name": "Twisted Ahriman", "base_monster_id": "ahriman",
        "description": "A warped watcher that assails foes with sinister magic.", "threat": "Severe",
        "bonus_min": 5, "bonus_max": 9, "hp_mult": 1.20, "power_mult": 1.10, "reward_mult": 1.40,
        "art": "/world-events/a1/twisted_ahriman.webp",
    },
    {
        "id": "ravenous_dragon", "name": "Ravenous Dragon", "base_monster_id": "red_dragon",
        "description": "A relentless drake driven by hunger and fury.", "threat": "Extreme",
        "bonus_min": 6, "bonus_max": 10, "hp_mult": 1.38, "power_mult": 1.10, "reward_mult": 1.45,
        "art": "/world-events/a1/ravenous_dragon.webp",
    },
    {
        "id": "bloodied_deathclaw", "name": "Bloodied Deathclaw", "base_monster_id": "death_claw",
        "description": "A frenzied beast that tears through the unwary with savage force.", "threat": "Severe",
        "bonus_min": 5, "bonus_max": 9, "hp_mult": 1.24, "power_mult": 1.12, "reward_mult": 1.40,
        "art": "/world-events/a1/bloodied_deathclaw.webp",
    },
)
WORLD_EVENTS_BY_ID = {row["id"]: row for row in WORLD_EVENTS}
