from __future__ import annotations

import copy
from typing import Any

DUNGEON_CACHE_RETREAT_RATIO = 0.50
DUNGEON_CACHE_DEFEAT_RATIO = 0.25
DUNGEON_COOLDOWN_SECONDS = 10 * 60


# Atmospheric details are cosmetic and saved with each run. No reward, monster,
# route, or boss mechanics depend on these strings.
DUNGEON_STORIES: dict[str, dict[str, Any]] = {
    "forgotten_ossuary": {
        "titles": ["The Bell Beneath the Crypt", "The Mourning Vigil", "Whispers in the Ossuary"],
        "mood": "Dust, candlelight, and the unsettled dead",
        "scenes": {
            "entrance": ["A bell tolls once from somewhere beneath the stone. No rope moves.", "Names vanish beneath your fingers as you brush dust from the crypt gate."],
            "combat": ["A procession of bones shifts in the dark. Something is counting your footsteps.", "The candle flames tilt toward the passage, though there is no wind."],
            "choice": ["A split corridor bears two different funeral blessings. Neither has aged kindly.", "A pale handprint marks the safe-looking arch; a second handprint marks the other."],
            "event": ["A whispered prayer breaks apart into a dozen different voices.", "For an instant, you hear the footsteps of a party that is not there."],
            "hazard": ["The floor groans under its own burial stones, and the air fills with grit."],
            "treasure": ["An untouched offering bowl gleams between centuries-old grave goods."],
            "miniboss": ["A warded tomb opens from within. Its defender remembers the old oaths."],
            "sanctuary": ["Gentle candlelight clings to a forgotten shrine and steadies your pulse."],
            "boss": ["At the heart of the dead city, the final guardian unfolds its wings."],
        },
    },
    "emberglass_foundry": {
        "titles": ["The Furnace That Dreams", "Embers Beneath the Mountain", "Last Shift at the Foundry"],
        "mood": "Furnace heat, clanging steel, and emberglass sparks",
        "scenes": {
            "entrance": ["A rusted shift bell rings through the deserted forge. The furnaces answer.", "Every anvil is cold, yet orange light pulses behind the sealed doors."],
            "combat": ["Something moves behind the slag curtain as the conveyor lurches to life.", "A spray of sparks reveals another shadow on the opposite gantry."],
            "choice": ["Two furnace valves rattle at once; only one corridor remains cool.", "An old foreman's warning is still chalked above a split in the catwalk."],
            "event": ["A machine coughs awake, then offers a single impossible chance."],
            "hazard": ["Molten glass creeps across the seams in the floor."],
            "treasure": ["An abandoned smith's cache survived the last collapse."],
            "miniboss": ["The forge's last watchman strides through sparks and smoke."],
            "sanctuary": ["A cooling chamber exhales clean air for the first time in ages."],
            "boss": ["The master furnace bursts open. Its keeper has not forgotten fire."],
        },
    },
    "whiteglass_bastion": {
        "titles": ["The White Watch", "Frost in the Watchtowers", "The Bastion's Last Signal"],
        "mood": "Frost-glass ramparts and a silence broken by steel",
        "scenes": {
            "entrance": ["The gate opens a hand's width; a frozen bugle sounds beyond it."],
            "combat": ["Bootprints appear in untouched snow ahead of you. No one is visible."],
            "choice": ["A signal fire and a frost-covered stairway offer different dangers."],
            "event": ["An old command echoes through the bastion's crystal speaking tubes."],
            "hazard": ["A bridge of whiteglass fractures under the weight of forgotten armor."],
            "treasure": ["A frozen supply locker bears the crest of the last watch."],
            "miniboss": ["The watch captain's guardian refuses to stand down."],
            "sanctuary": ["A sheltered barracks still holds warmth beneath the snow."],
            "boss": ["Beyond the final battlement, something ancient watches the blizzard."],
        },
    },
    "riftglass_observatory": {
        "titles": ["A Map of Broken Stars", "The Observatory Between Hours", "Shards of Tomorrow"],
        "mood": "Distorted starlight and impossible distances",
        "scenes": {
            "entrance": ["A star chart marks your arrival before you enter the observatory."],
            "combat": ["The corridor folds into itself, returning a shadow that was not yours."],
            "choice": ["Three constellations point toward two doors. One of the stars blinks."],
            "event": ["An hourglass pours upward as a voice warns of an unmade future."],
            "hazard": ["Gravity slips sideways; the glass beneath you holds for one breath."],
            "treasure": ["A lockbox is suspended in a ring of motionless crystal fragments."],
            "miniboss": ["The astral ward answers your presence with a fierce, familiar shape."],
            "sanctuary": ["Time slows enough to let your heart find its rhythm again."],
            "boss": ["The telescope turns toward a sky that should not exist."],
        },
    },
    "crystal_sanctum": {"titles": ["The Refracted Pilgrimage", "Echoes of the Sanctum"], "mood": "Singing wards and mirrored crystal", "scenes": {"entrance": ["The doorway shows a reflection of a stranger carrying your weapon."], "combat": ["A crystalline chord strikes as a sentinel wakes behind the glass."], "event": ["An unstable shard hums with an invitation and a warning."], "boss": ["The final mirror breaks. Its guardian steps through the light."]}},
    "abyssal_foundry": {"titles": ["The Black Furnace", "The Anvil of Ruin"], "mood": "Soot-dark metal and abyssal flame", "scenes": {"entrance": ["A hammer strikes the dark, though the forge stands empty."], "combat": ["Ash gathers into a living silhouette on the hot iron."], "event": ["A forbidden ingot pulses with something more than heat."], "boss": ["The anvil splits as the true forge guardian rises."]}},
    "celestial_spire": {"titles": ["Stairway to the Stars", "The Spire's Oath"], "mood": "Thin air and high celestial light", "scenes": {"entrance": ["A distant choir falters when you cross the threshold."], "combat": ["A spear of pale light strikes the stair and a defender appears."], "event": ["The sky briefly reflects a path you have yet to walk."], "boss": ["The clouds part to reveal the keeper of the highest step."]}},
    "void_cathedral": {"titles": ["The Silent Sermon", "Beneath the Empty Choir"], "mood": "Void-lit stained glass and a hollow hymn", "scenes": {"entrance": ["The cathedral bells ring without making a sound."], "combat": ["A dark hymn draws a shape from the last row of pews."], "event": ["A sealed book opens to a page bearing your name."], "boss": ["At the altar, the hymn ends. Something answers the silence."]}},
    "astral_crucible": {"titles": ["The Astral Trial", "The Furnace of Stars"], "mood": "Starlit metal and overwhelming pressure", "scenes": {"entrance": ["The crucible ignites with the light of a thousand stars."], "combat": ["The air hardens around you; a defender steps into the pressure."], "event": ["A star fragment drifts close enough to touch, but never falls."], "boss": ["The forge's heart flashes white as its master arrives."]}},
    "throne_eternity": {"titles": ["The Last Court", "The Crown Beyond Time"], "mood": "A royal hall outside the passing of time", "scenes": {"entrance": ["The throne room's clock has no hands, yet you hear it ticking."], "combat": ["A royal guard bows before lifting its weapon."], "event": ["A forgotten proclamation names a king who never lived."], "boss": ["The throne casts a shadow before its sovereign appears."]}},
}

GENERIC_SCENES = {
    "choice": ["Two paths disappear into the unknown. Your decision changes the danger ahead.", "A weathered sign points toward safety; the scratched-out arrow points toward reward."],
    "hazard": ["The chamber shifts unexpectedly. Watch your footing.", "An old trap stirs beneath the stones."],
    "treasure": ["Something valuable has survived the years, but the chamber may not be empty."],
    "sanctuary": ["A rare calm settles over this corner of the dungeon."],
    "miniboss": ["An elite guardian claims the passage and blocks the way forward."],
}


def decorate_dungeon_run_rooms(dungeon: dict[str, Any], rooms: list[dict[str, Any]], rng: Any) -> list[dict[str, Any]]:
    """Give each new standard/advanced dungeon route a saved story without changing mechanics."""
    theme = DUNGEON_STORIES.get(str(dungeon.get("id") or ""), {})
    scenes = theme.get("scenes") or {}
    titles = theme.get("titles") or [str(dungeon.get("name") or "Dungeon")]
    story_title = str(rng.choice(titles))
    for i, room in enumerate(rooms):
        kind = str(room.get("type") or "").lower()
        options = scenes.get(kind) or GENERIC_SCENES.get(kind) or []
        if options:
            room["story"] = str(rng.choice(options))
        room["story_chapter"] = "Finale" if kind == "boss" else "Prologue" if i == 0 else "Chapter " + str(i)
    if rooms:
        rooms[0]["story_title"] = story_title
        rooms[0]["story_mood"] = str(theme.get("mood") or "A road into the unknown")
    return rooms


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
    return decorate_dungeon_run_rooms(dungeon, run, rng)


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
    return decorate_dungeon_run_rooms(dungeon, unique, rng)
