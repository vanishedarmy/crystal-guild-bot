from __future__ import annotations

import copy
from typing import Any

DUNGEON_CACHE_RETREAT_RATIO = 0.50
DUNGEON_CACHE_DEFEAT_RATIO = 0.25


def room_kind_label(room: dict[str, Any]) -> str:
    kind = str(room.get("type") or "room").strip().lower()
    return {
        "entrance": "Entrance", "combat": "Encounter", "treasure": "Treasure",
        "hazard": "Hazard", "event": "Dungeon Event", "choice": "Crossroads",
        "miniboss": "Miniboss", "sanctuary": "Sanctuary", "boss": "Boss",
    }.get(kind, kind.replace("_", " ").title() or "Room")


def generate_ascension_dungeon_rooms(dungeon: dict[str, Any], monsters: dict[str, Any], rng: Any) -> list[dict[str, Any]]:
    """Vary high-level six-room dungeons while preserving original boss scripts.

    These are the six advanced Ascension Dungeons, *not* the 72 Job Trials.
    The signature ward and final guardian retain their authored combat phases;
    only the ward's monster and an extra normal encounter vary by run.
    """
    authored = copy.deepcopy(list(dungeon.get("rooms") or []))
    variants = dungeon.get("run_variants") or {}
    by_kind = {row.get("type"): row for row in authored}
    if not all(kind in by_kind for kind in ("entrance", "combat", "choice", "hazard", "sanctuary", "boss")):
        return authored
    entrance = by_kind["entrance"]
    ward = by_kind["combat"]
    choice = by_kind["choice"]
    hazard = by_kind["hazard"]
    sanctuary = by_kind["sanctuary"]
    boss = by_kind["boss"]
    boss_id = str(boss.get("monster_id") or "")
    rec = int(dungeon.get("recommended_level") or dungeon.get("min_level") or 1)
    pool = [str(mid) for mid in variants.get("encounter_pool") or []
            if mid in monsters and str(mid) != boss_id and rec - 11 <= int(monsters[mid].get("level", rec)) <= rec + 8]
    if len(pool) < 2:
        return authored
    rng.shuffle(pool)
    primary_id, side_id = pool[:2]
    authored_ward_id = str(ward.get("monster_id") or "")
    ward["monster_id"] = primary_id
    if primary_id != authored_ward_id:
        ward["name"] = f"Warded Guardian — {monsters[primary_id]['name']}"
        ward["description"] = f"{monsters[primary_id]['name']} guards a shifting ward. Watch its changing affinities and incoming attacks."
    side = copy.deepcopy(ward)
    side["id"] = "run_side_encounter"
    side["monster_id"] = side_id
    side["name"] = rng.choice(list(variants.get("ambience") or ["Side Passage"]))
    side["description"] = f"A wandering {monsters[side_id]['name']} blocks the unfamiliar passage."
    # New random battle is a normal encounter, not a second advanced boss.
    for field in ("advanced_combat", "mechanics", "opening_damage_percent", "opening_resource_drain_percent", "enemy_statuses"):
        side.pop(field, None)
    side["hp_multiplier"] = 0.88
    hazard["damage_percent"] = max(6, min(16, int(hazard.get("damage_percent", 10)) + rng.randint(-3, 3)))
    sanctuary["hp_restore_percent"] = max(18, min(40, int(sanctuary.get("hp_restore_percent", 25)) + rng.randint(-4, 5)))
    event_templates = list(variants.get("events") or [])
    rng.shuffle(event_templates)

    def event_room(template: dict[str, Any], index: int) -> dict[str, Any]:
        return {"id": f"run_aether_event_{index}", "type": "event", "name": str(template.get("name") or "Aether Event"),
                "description": str(template.get("description") or "The passage changes unexpectedly."),
                "outcomes": copy.deepcopy(list(template.get("outcomes") or []))}

    main_event = event_room(event_templates[0], 1)
    # Choice and ward alternate order; sanctuary always precedes final boss.
    patterns = [
        [entrance, choice, ward, hazard, main_event, side, sanctuary, boss],
        [entrance, ward, choice, hazard, side, main_event, sanctuary, boss],
        [entrance, choice, main_event, side, ward, hazard, sanctuary, boss],
    ]
    run = rng.choice(patterns)
    if len(event_templates) > 1 and rng.random() < 0.40:
        # Optional extra event makes run length and the adventure rhythm vary.
        run.insert(-2, event_room(event_templates[1], 2))
    return run


def generate_dungeon_run_rooms(dungeon: dict[str, Any], monsters: dict[str, Any], rng: Any) -> list[dict[str, Any]]:
    """Build a run-specific route from authored dungeon rooms.

    Every room is snapshotted in the player run at entry, rather than regenerated
    on each Portal refresh. Trials deliberately remain deterministic. The final
    boss, authored combat modifiers, completion reward and first-clear reward
    are never changed by this generator.
    """
    authored = copy.deepcopy(list(dungeon.get("rooms") or []))
    variants = dungeon.get("run_variants") or {}
    if dungeon.get("ascension_trial") or not variants:
        return authored
    if str(dungeon.get("identity") or "").lower() == "ascension dungeon":
        return generate_ascension_dungeon_rooms(dungeon, monsters, rng)

    def first(kind: str) -> dict[str, Any] | None:
        return next((copy.deepcopy(room) for room in authored if room.get("type") == kind), None)

    entrance, boss = first("entrance"), first("boss")
    combat, miniboss = first("combat"), first("miniboss")
    treasure, hazard, sanctuary = first("treasure"), first("hazard"), first("sanctuary")
    choices = [copy.deepcopy(row) for row in authored if row.get("type") == "choice"]
    if not all((entrance, boss, combat, miniboss, treasure, hazard, sanctuary)):
        return authored
    if str(boss.get("monster_id")) not in monsters:
        return authored

    recommended = int(dungeon.get("recommended_level") or dungeon.get("min_level") or 1)
    # Dungeon-specific, level-bounded ecology: no raid/world-event bosses,
    # unobtainable monster ids, or wildly over-levelled random enemies.
    def pool(key: str, fallback: str) -> list[str]:
        result = []
        for monster_id in variants.get(key) or []:
            row = monsters.get(str(monster_id))
            if (row and str(monster_id) not in result and
                    recommended - 12 <= int(row.get("level", recommended)) <= recommended + 12 and
                    monster_id != boss.get("monster_id")):
                result.append(str(monster_id))
        return result or [fallback]

    pool_ids = pool("encounter_pool", str(combat.get("monster_id")))
    rng.shuffle(pool_ids)
    selected = pool_ids[:2]
    if len(selected) == 1:
        selected *= 2  # configuration fallback only; all shipped pools have 6
    scenery = list(variants.get("ambience") or [str(combat.get("name") or "Deep Passage")])
    rng.shuffle(scenery)
    fight_rooms: list[dict[str, Any]] = []
    for index, monster_id in enumerate(selected):
        room = copy.deepcopy(combat)
        room["id"] = f"run_encounter_{index + 1}"
        room["name"] = str(scenery[index % len(scenery)])
        room["monster_id"] = monster_id
        room["description"] = f"{monsters[monster_id]['name']} stalks this passage. The route is different from the last expedition."
        # Two combat rooms are offset by a gentle HP range, not the extreme
        # scaling applied to high-tier Raid and World Event bosses.
        room["hp_multiplier"] = round(rng.uniform(0.94, 1.07), 2)
        fight_rooms.append(room)

    elite_pool = [mid for mid in pool("elite_pool", str(miniboss.get("monster_id"))) if mid not in selected]
    elite_id = rng.choice(elite_pool) if elite_pool else str(miniboss.get("monster_id"))
    miniboss["monster_id"] = elite_id
    if elite_id != str(first("miniboss").get("monster_id")):
        miniboss["name"] = f"Elite Guardian — {monsters[elite_id]['name']}"
        miniboss["description"] = f"An empowered {monsters[elite_id]['name']} holds the approach to the inner sanctum."

    event_templates = list(variants.get("events") or [])
    if event_templates:
        event_template = copy.deepcopy(rng.choice(event_templates))
        event_room = {
            "id": "run_event", "type": "event", "name": str(event_template.get("name") or "Unknown Occurrence"),
            "description": str(event_template.get("description") or "Something unusual happens."),
            "outcomes": copy.deepcopy(list(event_template.get("outcomes") or [])),
        }
    else:
        event_room = first("event")

    # Branches vary in order and length. Every run has at least one real route
    # decision or event, two normal encounters, an elite and its familiar boss.
    branch = rng.choice(choices) if choices else event_room
    if event_room and choices and rng.random() < 0.35:
        branch = event_room
    # Guarantee both a crossroads and a random event, but vary their order.
    mandatory = event_room if branch is not event_room else rng.choice(choices)
    # Existing choices may ward the next hazard. Keep one in every new run so
    # the previewed protection has a real opportunity to pay off.
    center = [mandatory, hazard]
    if rng.random() < 0.5:
        center.append(treasure)
    rng.shuffle(center)
    hazard["damage_percent"] = max(5, min(18, int(hazard.get("damage_percent", 10)) + rng.randint(-4, 4)))
    treasure["gil"] = max(0, round(int(treasure.get("gil", 0)) * rng.uniform(0.80, 1.15)))
    sanctuary["hp_restore_percent"] = max(15, min(40, int(sanctuary.get("hp_restore_percent", 25)) + rng.randint(-5, 7)))

    # Move the rest point either before or after the elite. The boss is always last.
    before_elite = rng.random() < 0.35
    run = [entrance, branch, fight_rooms[0], *center, fight_rooms[1]]
    if before_elite:
        run.append(sanctuary)
    run.append(miniboss)
    if not before_elite:
        run.append(sanctuary)
    run.append(boss)
    # An event/choice selected twice is deduplicated, while all other IDs stay
    # stable for request-id validation and browser refreshes.
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for room in run:
        if room is None:
            continue
        rid = str(room.get("id") or "")
        if rid in seen:
            continue
        seen.add(rid)
        unique.append(room)
    return unique
