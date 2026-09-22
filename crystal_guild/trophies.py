from __future__ import annotations

import json
import sqlite3
from typing import Any

# Hall of Trophies Phase 1. IDs are permanent save-data keys; display names and
# descriptions may evolve without invalidating earned ownership.
TROPHY_CATALOG: tuple[dict[str, Any], ...] = (
    {"id":"we_notorious_behemoth","category":"world_events","name":"Horn of the Notorious","description":"A horn taken from the Notorious Behemoth, proof that you stood against one of the realm's fiercest World Events.","art":"/trophies/a1/world-events/horn-of-the-notorious.webp","requirement":"Defeat Notorious Behemoth in a World Event.","unlock":{"kind":"world_event","id":"notorious_behemoth"}},
    {"id":"we_tainted_malboro","category":"world_events","name":"Breath of Blight","description":"A preserved specimen from the Tainted Malboro and its ruinous breath.","art":"/trophies/a1/world-events/breath-of-blight.webp","requirement":"Defeat Tainted Malboro in a World Event.","unlock":{"kind":"world_event","id":"tainted_malboro"}},
    {"id":"we_dark_iron_giant","category":"world_events","name":"Black Iron Crest","description":"A shattered crest from the Dark Iron Giant's immense armor.","art":"/trophies/a1/world-events/black-iron-crest.webp","requirement":"Defeat Dark Iron Giant in a World Event.","unlock":{"kind":"world_event","id":"dark_iron_giant"}},
    {"id":"we_elder_adamantoise","category":"world_events","name":"Elder's Carapace","description":"A weathered fragment of the Elder Adamantoise's ancient shell.","art":"/trophies/a1/world-events/elders-carapace.webp","requirement":"Defeat Elder Adamantoise in a World Event.","unlock":{"kind":"world_event","id":"elder_adamantoise"}},
    {"id":"we_cursed_tonberry_king","category":"world_events","name":"The King's Lantern","description":"The royal lantern left behind by the Cursed Tonberry King.","art":"/trophies/a1/world-events/the-kings-lantern.webp","requirement":"Defeat Cursed Tonberry King in a World Event.","unlock":{"kind":"world_event","id":"cursed_tonberry_king"}},
    {"id":"we_savage_coeurl","category":"world_events","name":"Stormwhisker","description":"A lightning-scarred relic from the Savage Coeurl.","art":"/trophies/a1/world-events/stormwhisker.webp","requirement":"Defeat Savage Coeurl in a World Event.","unlock":{"kind":"world_event","id":"savage_coeurl"}},
    {"id":"we_dread_bomb_king","category":"world_events","name":"Crown of Cinders","description":"A crown tempered in the blast of the Dread Bomb King.","art":"/trophies/a1/world-events/crown-of-cinders.webp","requirement":"Defeat Dread Bomb King in a World Event.","unlock":{"kind":"world_event","id":"dread_bomb_king"}},
    {"id":"we_twisted_ahriman","category":"world_events","name":"Eye of the Twisted","description":"An unsettling trophy taken from the Twisted Ahriman.","art":"/trophies/a1/world-events/eye-of-the-twisted.webp","requirement":"Defeat Twisted Ahriman in a World Event.","unlock":{"kind":"world_event","id":"twisted_ahriman"}},
    {"id":"we_ravenous_dragon","category":"world_events","name":"Ravenous Fang","description":"A massive fang from the Ravenous Dragon's final charge.","art":"/trophies/a1/world-events/ravenous-fang.webp","requirement":"Defeat Ravenous Dragon in a World Event.","unlock":{"kind":"world_event","id":"ravenous_dragon"}},
    {"id":"we_bloodied_deathclaw","category":"world_events","name":"Bloodied Talon","description":"A brutal talon claimed from the Bloodied Deathclaw.","art":"/trophies/a1/world-events/bloodied-talon.webp","requirement":"Defeat Bloodied Deathclaw in a World Event.","unlock":{"kind":"world_event","id":"bloodied_deathclaw"}},
    {"id":"we_all_phase1","category":"world_events","name":"Notorious Menagerie","description":"The complete first collection of World Event trophies gathered into one crest.","art":"/trophies/a1/world-events/notorious-menagerie.webp","requirement":"Earn all 10 World Event trophies.","unlock":{"kind":"trophy_set","ids":["we_notorious_behemoth","we_tainted_malboro","we_dark_iron_giant","we_elder_adamantoise","we_cursed_tonberry_king","we_savage_coeurl","we_dread_bomb_king","we_twisted_ahriman","we_ravenous_dragon","we_bloodied_deathclaw"]}},
    {"id":"raid_ifrit","category":"raids","name":"Ember of Ifrit","description":"A burning crystal ember displayed in remembrance of victory over Ifrit.","art":"/trophies/a1/raids/ember-of-ifrit.webp","requirement":"Clear the Ifrit Raid.","unlock":{"kind":"raid_clear","id":"ifrit"}},
    {"id":"raid_shiva","category":"raids","name":"Diamond of Shiva","description":"An impossible shard of ice preserved from Shiva's frozen throne.","art":"/trophies/a1/raids/diamond-of-shiva.webp","requirement":"Clear the Shiva Raid.","unlock":{"kind":"raid_clear","id":"shiva"}},
    {"id":"raid_titan","category":"raids","name":"Heart of the Crag","description":"A stone heart still glowing with the force of Titan's domain.","art":"/trophies/a1/raids/heart-of-the-crag.webp","requirement":"Clear the Titan Raid.","unlock":{"kind":"raid_clear","id":"titan"}},
    {"id":"raid_bahamut","category":"raids","name":"Shard of the Final Coil","description":"A draconic crystal shard recovered after conquering Bahamut's Final Coil.","art":"/trophies/a1/raids/shard-of-the-final-coil.webp","requirement":"Clear the Bahamut Raid.","unlock":{"kind":"raid_clear","id":"bahamut"}},
    {"id":"raid_primals","category":"raids","name":"Primal Conqueror","description":"A sixfold crest honoring mastery over the Guild's original Primal trials.","art":"/trophies/a1/raids/primal-conqueror.webp","requirement":"Clear Ifrit, Shiva, Ramuh, Garuda, Titan, and Leviathan.","unlock":{"kind":"raid_set","ids":["ifrit","shiva","ramuh","garuda_prime","titan","leviathan"]}},
    {"id":"hunt_tyrant","category":"hunts","name":"Tyrant's Crown","description":"A grim crown mounted for the hunter who brought down the Tyrant of the Rift.","art":"/trophies/a1/hunts/tyrants-crown.webp","requirement":"Clear Tyrant of the Rift.","unlock":{"kind":"hunt_clear","id":"tyrant_of_the_rift"}},
    {"id":"hunt_mountain","category":"hunts","name":"The Mountain's Plate","description":"An enormous armored plate claimed when the Mountain finally stopped moving.","art":"/trophies/a1/hunts/the-mountains-plate.webp","requirement":"Clear The Mountain Moves.","unlock":{"kind":"hunt_clear","id":"the_mountain_moves"}},
    {"id":"hunt_veilscale","category":"hunts","name":"Veilscale","description":"An iridescent scale from the dragon beyond the veil.","art":"/trophies/a1/hunts/veilscale.webp","requirement":"Clear Dragon Beyond the Veil.","unlock":{"kind":"hunt_clear","id":"dragon_beyond_the_veil"}},
    {"id":"hunt_srank_all","category":"hunts","name":"S-Rank Bounty Board","description":"A completed board bearing the marks of every current S-Rank Hunt.","art":"/trophies/a1/hunts/s-rank-bounty-board.webp","requirement":"Clear all 3 current S-Rank Hunts.","unlock":{"kind":"hunt_set","ids":["tyrant_of_the_rift","the_mountain_moves","dragon_beyond_the_veil"]}},
    {"id":"tt_first_win","category":"triple_triad","name":"Opening Hand","description":"The first winning hand in a growing Triple Triad career.","art":"/trophies/a1/triple-triad/opening-hand.webp","requirement":"Win a Triple Triad match.","unlock":{"kind":"triple_triad_wins","target":1}},
    {"id":"tt_streak_3","category":"triple_triad","name":"Hot Streak","description":"Three victories in succession, remembered in flame and gold.","art":"/trophies/a1/triple-triad/hot-streak.webp","requirement":"Reach a 3-win Triple Triad streak.","unlock":{"kind":"triple_triad_streak","target":3}},
    {"id":"tt_cards_10","category":"triple_triad","name":"Collector's Folio","description":"A carefully kept folio celebrating a collection of ten unique cards.","art":"/trophies/a1/triple-triad/collectors-folio.webp","requirement":"Own 10 unique Triple Triad cards.","unlock":{"kind":"triple_triad_cards","target":10}},
    {"id":"tt_cards_all","category":"triple_triad","name":"Master Deck","description":"The complete original fifteen-card collection displayed as a master set.","art":"/trophies/a1/triple-triad/master-deck.webp","requirement":"Own all 15 current Triple Triad cards.","unlock":{"kind":"triple_triad_card_set","ids":["chocobo","moogle","cactuar","bomb","flan","tonberry","coeurl","ahriman","malboro","ifrit","shiva","ramuh","leviathan","bahamut","odin"]}},
    {"id":"fellowship_guildhall_3","category":"fellowship","name":"Crystal Foundation","description":"A miniature of the Guild Hall honoring those who helped raise it to Lv. 3.","art":"/trophies/a1/fellowship/crystal-foundation.webp","requirement":"Contribute to Guild Hall Lv. 3 before its completion.","unlock":{"kind":"fellowship_project","project_id":"guild_hall_t3","facility_id":"guild_hall","tier":3}},
    {"id":"fellowship_workshop_3","category":"fellowship","name":"Masterwork Anvil","description":"The Fellowship's forge immortalized for a contributor to Workshop Lv. 3.","art":"/trophies/a1/fellowship/masterwork-anvil.webp","requirement":"Contribute to Workshop Lv. 3 before its completion.","unlock":{"kind":"fellowship_project","project_id":"workshop_t3","facility_id":"workshop","tier":3}},
    {"id":"fellowship_archive_3","category":"fellowship","name":"Living Archive","description":"An enchanted archive honoring contributors to Guild Archive Lv. 3.","art":"/trophies/a1/fellowship/living-archive.webp","requirement":"Contribute to Guild Archive Lv. 3 before its completion.","unlock":{"kind":"fellowship_project","project_id":"archives_t3","facility_id":"archives","tier":3}},
    {"id":"fellowship_airship_3","category":"fellowship","name":"Skybound Berth","description":"A model of the completed Airship Dock and the journeys it made possible.","art":"/trophies/a1/fellowship/skybound-berth.webp","requirement":"Contribute to Airship Dock Lv. 3 before its completion.","unlock":{"kind":"fellowship_project","project_id":"airship_dock_t3","facility_id":"airship_dock","tier":3}},
    {"id":"fellowship_annex","category":"fellowship","name":"Kupo Expansion Permit","description":"A cheerful permit commemorating construction of the Moogle Emporium Annex.","art":"/trophies/a1/fellowship/kupo-expansion-permit.webp","requirement":"Contribute to the Moogle Emporium Annex before its completion.","unlock":{"kind":"fellowship_project","project_id":"emporium_annex_t1","facility_id":"emporium_annex","tier":1}},
    {"id":"fellowship_trading_post","category":"fellowship","name":"Merchant's Bell","description":"The market bell rung for those who helped establish the Moogle Trading Post.","art":"/trophies/a1/fellowship/merchants-bell.webp","requirement":"Contribute to the Moogle Trading Post before its completion.","unlock":{"kind":"fellowship_project","project_id":"trading_post_t1","facility_id":"trading_post","tier":1}},
)

TROPHIES_BY_ID = {row["id"]: row for row in TROPHY_CATALOG}
CATEGORY_ORDER = ("world_events", "raids", "hunts", "triple_triad", "fellowship")


def _json_ids(value: Any) -> set[str]:
    try:
        parsed = json.loads(value or "[]")
    except (TypeError, ValueError, json.JSONDecodeError):
        parsed = []
    return {str(item) for item in parsed} if isinstance(parsed, list) else set()


def _has_clear(conn: sqlite3.Connection, table: str, id_column: str, player_id: str, value: str) -> bool:
    row = conn.execute(
        f"SELECT 1 FROM {table} WHERE player_id=? AND {id_column}=? AND clears>0 LIMIT 1",
        (player_id, value),
    ).fetchone()
    return bool(row)


def _qualifies(conn: sqlite3.Connection, player_id: str, trophy: dict[str, Any]) -> bool:
    unlock = trophy["unlock"]
    kind = str(unlock["kind"])
    if kind == "world_event":
        return _has_clear(conn, "player_world_event_clears", "world_event_id", player_id, str(unlock["id"]))
    if kind == "raid_clear":
        return _has_clear(conn, "player_boss_clears", "boss_id", player_id, str(unlock["id"]))
    if kind == "raid_set":
        return all(_has_clear(conn, "player_boss_clears", "boss_id", player_id, str(value)) for value in unlock["ids"])
    if kind == "hunt_clear":
        return _has_clear(conn, "player_hunts", "hunt_id", player_id, str(unlock["id"]))
    if kind == "hunt_set":
        return all(_has_clear(conn, "player_hunts", "hunt_id", player_id, str(value)) for value in unlock["ids"])
    if kind in {"triple_triad_wins", "triple_triad_streak", "triple_triad_cards", "triple_triad_card_set"}:
        row = conn.execute(
            "SELECT collection_json,wins,best_streak FROM player_triple_triad WHERE player_id=?",
            (player_id,),
        ).fetchone()
        if not row:
            return False
        if kind == "triple_triad_wins":
            return int(row["wins"] or 0) >= int(unlock["target"])
        if kind == "triple_triad_streak":
            return int(row["best_streak"] or 0) >= int(unlock["target"])
        owned = _json_ids(row["collection_json"])
        if kind == "triple_triad_cards":
            return len(owned) >= int(unlock["target"])
        return set(str(value) for value in unlock["ids"]).issubset(owned)
    if kind == "fellowship_project":
        member = conn.execute(
            "SELECT 1 FROM fellowship_project_members WHERE project_id=? AND player_id=? LIMIT 1",
            (str(unlock["project_id"]), player_id),
        ).fetchone()
        facility = conn.execute(
            "SELECT tier FROM fellowship_facilities WHERE facility_id=?",
            (str(unlock["facility_id"]),),
        ).fetchone()
        return bool(member and facility and int(facility["tier"] or 0) >= int(unlock["tier"]))
    if kind == "trophy_set":
        required = {str(value) for value in unlock["ids"]}
        if not required:
            return False
        placeholders = ",".join("?" for _ in required)
        row = conn.execute(
            f"SELECT COUNT(*) AS n FROM player_trophies WHERE player_id=? AND trophy_id IN ({placeholders})",
            (player_id, *sorted(required)),
        ).fetchone()
        return int(row["n"] or 0) >= len(required)
    return False


def reconcile_player_trophies(conn: sqlite3.Connection, player_id: str, *, source: str = "reconciliation") -> list[str]:
    """Award every provable trophy to a player, safely and idempotently."""
    awarded: list[str] = []
    # Two passes are enough for Phase 1 because only Notorious Menagerie depends
    # on trophy ownership, but retain a generic fixed-point loop for expansion.
    for _ in range(max(1, len(TROPHY_CATALOG) + 1)):
        changed = False
        for trophy in TROPHY_CATALOG:
            trophy_id = str(trophy["id"])
            exists = conn.execute(
                "SELECT 1 FROM player_trophies WHERE player_id=? AND trophy_id=?",
                (player_id, trophy_id),
            ).fetchone()
            if exists or not _qualifies(conn, player_id, trophy):
                continue
            cursor = conn.execute(
                "INSERT OR IGNORE INTO player_trophies(player_id,trophy_id,unlock_source) VALUES (?,?,?)",
                (player_id, trophy_id, str(source or "reconciliation")),
            )
            if cursor.rowcount:
                awarded.append(str(trophy["name"]))
                changed = True
        if not changed:
            break
    return awarded


def record_world_event_clear(conn: sqlite3.Connection, player_id: str, world_event_id: str) -> None:
    conn.execute(
        "INSERT INTO player_world_event_clears(player_id,world_event_id,clears,first_cleared_at,last_cleared_at) "
        "VALUES (?,?,1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP) "
        "ON CONFLICT(player_id,world_event_id) DO UPDATE SET clears=clears+1,last_cleared_at=CURRENT_TIMESTAMP",
        (str(player_id), str(world_event_id)),
    )
