from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class GameData:
    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)
        self.jobs = self._load_map("jobs.json")
        self.monsters = self._load_map("monsters.json")
        self.regions = self._load_map("regions.json")
        self.items = self._load_map("items.json")
        self.achievements = self._load_map("achievements.json")
        self.bosses = self._load_map("bosses.json")
        self.hunts = self._load_map("hunts.json")
        self.quests = self._load_map("quests.json")
        self.titles = self._load_map("titles.json")
        self.recipes = self._load_map("recipes.json")
        self.relics = self._load_map("relics.json")
        self.seal_shop = self._load_map("seal_shop.json")
        self.forge = sorted(self._load_list("forge.json"), key=lambda r: r["level"])
        self.active_abilities = self._load_active_abilities()
        self.enemy_profiles = self._load_map("enemy_profiles.json")
        self.enemy_actions = self._load_map("enemy_actions.json")

    def _load_map(self, filename: str) -> dict[str, dict[str, Any]]:
        payload = json.loads((self.data_dir / filename).read_text(encoding="utf-8"))
        result: dict[str, dict[str, Any]] = {}
        for entry in payload:
            entry_id = str(entry.get("id", "")).strip()
            if not entry_id:
                raise ValueError(f"{filename}: entry is missing a non-empty id")
            if entry_id in result:
                raise ValueError(f"{filename}: duplicate id {entry_id!r}")
            result[entry_id] = entry
        return result

    def _load_list(self, filename: str) -> list[dict[str, Any]]:
        return json.loads((self.data_dir / filename).read_text(encoding="utf-8"))

    def _load_active_abilities(self) -> dict[str, list[dict[str, Any]]]:
        """Load one active-ability catalog per Job without silent overwrites."""
        result: dict[str, list[dict[str, Any]]] = {}
        for row in self._load_list("active_abilities.json"):
            job_id = str(row.get("job_id", "")).strip()
            if not job_id:
                raise ValueError("active_abilities.json: entry is missing job_id")
            if job_id in result:
                raise ValueError(
                    f"active_abilities.json: duplicate Job catalog {job_id!r}"
                )
            result[job_id] = row.get("abilities", [])
        return result

    def validate(self) -> list[str]:
        errors: list[str] = []

        def require(collection: dict[str, Any], ref: str | None, where: str) -> None:
            if ref and ref not in collection:
                errors.append(f"{where}: unknown id {ref!r}")

        def chance(value: Any, where: str) -> None:
            try:
                parsed = float(value)
            except (TypeError, ValueError):
                errors.append(f"{where}: chance must be numeric")
                return
            if not 0 <= parsed <= 1:
                errors.append(f"{where}: chance out of range")

        valid_item_types = {"weapon", "armor", "accessory", "consumable", "material"}
        valid_rarities = {"common", "uncommon", "rare", "epic", "relic", "artifact", "legendary"}

        for job in self.jobs.values():
            if float(job.get("damage_mod", 0)) <= 0:
                errors.append(f"job {job['id']}: damage_mod must be > 0")
            resource_mode = str(job.get("resource_mode", "")).lower()
            if resource_mode not in {"mp", "ap", "dual"}:
                errors.append(f"job {job['id']}: resource_mode must be mp, ap, or dual")
            growth = job.get("growth", {})
            for stat in ("str", "vit", "mag", "spr", "dex", "lck"):
                if float(growth.get(stat, -1)) < 0:
                    errors.append(f"job {job['id']}: invalid growth {stat}")
            chance(job.get("signature_chance", 0), f"job {job['id']} signature")
            if job.get("heal_chance") is not None:
                chance(job.get("heal_chance", 0), f"job {job['id']} heal")
            previous = 0
            for ability in job.get("abilities", []):
                level = int(ability.get("level", 0))
                if not 1 <= level <= 50 or level <= previous:
                    errors.append(f"job {job['id']}: ability levels must increase within 1..50")
                previous = level

        # Active battle abilities are intentionally stored separately from
        # passive Job milestones. This keeps combat actions editable without
        # risking the long-standing passive progression schema.
        valid_targets = {"enemy", "self", "ally", "party"}
        valid_scaling = {"physical", "magic", "hybrid"}
        valid_resources = {"mp", "ap"}
        valid_effects = {
            "damage",
            "heal",
            "restore_mp",
            "restore_ap",
            "revive",
            "status",
            "cleanse",
            "drain",
        }
        valid_statuses = {
            "protect",
            "taunt",
            "evade",
            "power_up",
            "focus",
            "haste",
            "regen",
            "vulnerable",
            "weaken",
            "slow",
            "stun",
            "poison",
            "silence",
            "blind",
        }
        for job_id, abilities in self.active_abilities.items():
            require(self.jobs, job_id, "active ability job")
            if len(abilities) < 3:
                errors.append(f"active abilities {job_id}: expected at least 3 abilities")

            seen: set[str] = set()
            previous_level = 0
            for ability in abilities:
                aid = str(ability.get("id", "")).strip()
                if not aid or aid in seen:
                    errors.append(
                        f"active abilities {job_id}: missing/duplicate ability id {aid!r}"
                    )
                seen.add(aid)

                if not str(ability.get("name", "")).strip():
                    errors.append(f"active ability {job_id}:{aid}: missing name")
                if not str(ability.get("description", "")).strip():
                    errors.append(f"active ability {job_id}:{aid}: missing description")

                level = int(ability.get("level", 0))
                if not 1 <= level <= 50 or level < previous_level:
                    errors.append(
                        f"active ability {job_id}:{aid}: level must increase within 1..50"
                    )
                previous_level = level

                resource = str(ability.get("resource", "")).lower()
                if resource not in valid_resources:
                    errors.append(f"active ability {job_id}:{aid}: resource must be mp or ap")
                mode = str(self.jobs.get(job_id, {}).get("resource_mode", ""))
                if mode in {"mp", "ap"} and resource and resource != mode:
                    errors.append(f"active ability {job_id}:{aid}: {resource} is incompatible with {mode}-only Job")
                cost = int(ability.get("cost", ability.get("mp", -1)))
                if cost < 0:
                    errors.append(f"active ability {job_id}:{aid}: cost must be >= 0")
                if cost > 20:
                    errors.append(f"active ability {job_id}:{aid}: cost exceeds 20-point Active Battle guardrail")
                if ability.get("target") not in valid_targets:
                    errors.append(f"active ability {job_id}:{aid}: invalid target")

                effects = ability.get("effects", [])
                if not effects:
                    errors.append(f"active ability {job_id}:{aid}: no effects")
                for effect in effects:
                    effect_type = effect.get("type")
                    if effect_type not in valid_effects:
                        errors.append(
                            f"active ability {job_id}:{aid}: invalid effect {effect_type!r}"
                        )
                        continue
                    if effect_type == "damage":
                        if effect.get("scaling") not in valid_scaling:
                            errors.append(
                                f"active ability {job_id}:{aid}: invalid damage scaling"
                            )
                        power = float(effect.get("power", 0))
                        if power <= 0:
                            errors.append(
                                f"active ability {job_id}:{aid}: damage power must be > 0"
                            )
                        if power > 2.40:
                            errors.append(
                                f"active ability {job_id}:{aid}: damage power exceeds 2.40 balance guardrail"
                            )
                    elif effect_type == "heal":
                        power = float(effect.get("power", 0))
                        if power <= 0:
                            errors.append(
                                f"active ability {job_id}:{aid}: heal power must be > 0"
                            )
                        if power > 1.80:
                            errors.append(
                                f"active ability {job_id}:{aid}: heal power exceeds 1.80 balance guardrail"
                            )
                    elif effect_type in {"restore_mp", "restore_ap", "revive", "drain"}:
                        fraction = float(effect.get("fraction", -1))
                        if not 0 <= fraction <= 1:
                            errors.append(
                                f"active ability {job_id}:{aid}: {effect_type} fraction "
                                "must be within 0..1"
                            )
                        caps = {"restore_mp": 0.25, "restore_ap": 0.25, "revive": 0.50, "drain": 0.40}
                        if fraction > caps[effect_type]:
                            errors.append(
                                f"active ability {job_id}:{aid}: {effect_type} fraction exceeds "
                                f"{caps[effect_type]:.2f} balance guardrail"
                            )
                    elif effect_type == "cleanse":
                        if int(effect.get("count", 0)) < 1:
                            errors.append(
                                f"active ability {job_id}:{aid}: cleanse count must be >= 1"
                            )
                    elif effect_type == "status":
                        status_id = effect.get("status")
                        if status_id not in valid_statuses:
                            errors.append(
                                f"active ability {job_id}:{aid}: invalid status {status_id!r}"
                            )
                        turns = int(effect.get("turns", 0))
                        if turns < 1:
                            errors.append(
                                f"active ability {job_id}:{aid}: status turns must be >= 1"
                            )
                        if turns > 3:
                            errors.append(
                                f"active ability {job_id}:{aid}: status duration exceeds 3-round balance guardrail"
                            )
                        magnitude = float(effect.get("magnitude", 0.0))
                        status_caps = {
                            "protect": 0.40, "taunt": 3.0, "evade": 0.35,
                            "power_up": 0.20, "focus": 0.30, "haste": 0.15,
                            "regen": 0.20, "vulnerable": 0.20, "weaken": 0.20,
                            "slow": 0.30, "stun": 1.0, "poison": 0.08,
                            "silence": 0.0, "blind": 0.40,
                        }
                        cap = status_caps.get(str(status_id))
                        if cap is not None and magnitude > cap:
                            errors.append(
                                f"active ability {job_id}:{aid}: {status_id} magnitude exceeds "
                                f"{cap:.2f} balance guardrail"
                            )
                        if effect.get("chance") is not None:
                            chance(
                                effect.get("chance"),
                                f"active ability {job_id}:{aid} status",
                            )

        for job_id in self.jobs:
            if job_id not in self.active_abilities:
                errors.append(f"job {job_id}: missing active battle ability catalog")

        # Enemy combat data is intentionally separate from the base monster
        # ``special`` field used by other resolvers. That lets
        # Active Battle AI evolve without silently rebalance other modes.
        valid_enemy_targets = {"single", "party", "self"}
        valid_enemy_scaling = {"physical", "magic"}
        valid_enemy_effects = {"damage", "status", "heal_self", "drain", "recoil"}
        for profile in self.enemy_profiles.values():
            if float(profile.get("ability_bias", 0)) <= 0:
                errors.append(f"enemy profile {profile['id']}: ability_bias must be > 0")
            damage_mult = float(profile.get("damage_mult", 0))
            if damage_mult <= 0:
                errors.append(f"enemy profile {profile['id']}: damage_mult must be > 0")
            if damage_mult > 1.15:
                errors.append(f"enemy profile {profile['id']}: damage_mult exceeds 1.15 balance guardrail")
            utility = profile.get("utility") or {}
            if utility:
                chance(utility.get("chance", 0), f"enemy profile {profile['id']} utility")
                hp_below = float(utility.get("hp_below", -1))
                if not 0 <= hp_below <= 1:
                    errors.append(f"enemy profile {profile['id']}: utility hp_below out of range")
                if utility.get("status") not in valid_statuses:
                    errors.append(f"enemy profile {profile['id']}: invalid utility status")
                utility_turns = int(utility.get("turns", 0))
                if utility_turns < 1:
                    errors.append(f"enemy profile {profile['id']}: utility turns must be >= 1")
                if utility_turns > 3:
                    errors.append(f"enemy profile {profile['id']}: utility exceeds 3-round duration guardrail")
                if float(utility.get("magnitude", 0.0)) > 0.35:
                    errors.append(f"enemy profile {profile['id']}: utility magnitude exceeds 0.35 guardrail")

        for monster_id, behavior in self.enemy_actions.items():
            require(self.monsters, monster_id, "enemy action monster")
            require(self.enemy_profiles, behavior.get("profile"), f"enemy action {monster_id} profile")
            ability = behavior.get("ability") or None
            if not ability:
                continue
            if not str(ability.get("id", "")).strip() or not str(ability.get("name", "")).strip():
                errors.append(f"enemy action {monster_id}: ability needs id/name")
            chance(ability.get("chance", 0), f"enemy action {monster_id} ability")
            if int(ability.get("cooldown", 0)) < 1:
                errors.append(f"enemy action {monster_id}: cooldown must be >= 1")
            if ability.get("target") not in valid_enemy_targets:
                errors.append(f"enemy action {monster_id}: invalid target")
            if ability.get("scaling") not in valid_enemy_scaling:
                errors.append(f"enemy action {monster_id}: invalid scaling")
            enemy_power = float(ability.get("power", -1))
            if enemy_power < 0:
                errors.append(f"enemy action {monster_id}: power must be >= 0")
            if enemy_power > 1.50:
                errors.append(f"enemy action {monster_id}: power exceeds 1.50 balance guardrail")
            effects = ability.get("effects") or []
            if not effects:
                errors.append(f"enemy action {monster_id}: ability needs effects")
            for effect in effects:
                effect_type = effect.get("type")
                if effect_type not in valid_enemy_effects:
                    errors.append(f"enemy action {monster_id}: invalid effect {effect_type!r}")
                    continue
                if effect_type == "status":
                    if effect.get("status") not in valid_statuses:
                        errors.append(f"enemy action {monster_id}: invalid status")
                    enemy_turns = int(effect.get("turns", 0))
                    if enemy_turns < 1:
                        errors.append(f"enemy action {monster_id}: status turns must be >= 1")
                    if enemy_turns > 3:
                        errors.append(f"enemy action {monster_id}: status exceeds 3-round duration guardrail")
                    if float(effect.get("magnitude", 0.0)) > 0.40:
                        errors.append(f"enemy action {monster_id}: status magnitude exceeds 0.40 guardrail")
                    chance(effect.get("chance", 1), f"enemy action {monster_id} status")
                elif effect_type in {"heal_self", "drain", "recoil"}:
                    fraction = float(effect.get("fraction", -1))
                    if not 0 <= fraction <= 1:
                        errors.append(f"enemy action {monster_id}: {effect_type} fraction out of range")

        missing_enemy_actions = set(self.monsters) - set(self.enemy_actions)
        extra_enemy_actions = set(self.enemy_actions) - set(self.monsters)
        if missing_enemy_actions:
            errors.append(f"enemy actions missing monsters: {', '.join(sorted(missing_enemy_actions))}")
        if extra_enemy_actions:
            errors.append(f"enemy actions reference unknown monsters: {', '.join(sorted(extra_enemy_actions))}")

        for region in self.regions.values():
            encounters = region.get("encounters", [])
            if not encounters:
                errors.append(f"region {region['id']}: no encounters")
            for encounter in encounters:
                require(self.monsters, encounter.get("monster_id"), f"region {region['id']}")
                if float(encounter.get("weight", 0)) <= 0:
                    errors.append(f"region {region['id']}: encounter weight must be > 0")
            known = [
                self.monsters[encounter["monster_id"]]
                for encounter in encounters
                if encounter.get("monster_id") in self.monsters
            ]
            if known:
                minimum_entry_level = int(region.get("min_level", 1))
                if not any(int(monster.get("level", 0)) <= minimum_entry_level + 5 for monster in known):
                    errors.append(
                        f"region {region['id']}: no encounter is within +5 levels of its minimum entry level"
                    )

        harmful_statuses = {"vulnerable", "weaken", "slow", "stun", "poison", "silence", "blind"}
        valid_item_use_effects = {"heal_hp", "restore_mp", "restore_ap", "revive", "cleanse", "status", "damage"}

        for item in self.items.values():
            if item.get("type") not in valid_item_types:
                errors.append(f"item {item['id']}: invalid type")
            if item.get("rarity", "common") not in valid_rarities:
                errors.append(f"item {item['id']}: invalid rarity")
            if int(item.get("price", 0)) < 0:
                errors.append(f"item {item['id']}: price must be >= 0")
            for job_id in item.get("allowed_jobs", []):
                require(self.jobs, job_id, f"item {item['id']} allowed job")
            if item.get("shop"):
                if int(item.get("price", 0)) <= 0:
                    errors.append(f"item {item['id']}: shop price must be > 0")
                if int(item.get("shop_level", 1)) < 1:
                    errors.append(f"item {item['id']}: shop_level must be >= 1")

            use = item.get("use")
            if use is not None:
                if not isinstance(use, dict):
                    errors.append(f"item {item['id']}: use must be an object")
                else:
                    if use.get("target") not in valid_targets:
                        errors.append(f"item {item['id']}: invalid use target")
                    effects = use.get("effects") or []
                    if not effects:
                        errors.append(f"item {item['id']}: use needs effects")
                    for effect in effects:
                        effect_type = effect.get("type")
                        if effect_type not in valid_item_use_effects:
                            errors.append(f"item {item['id']}: invalid use effect {effect_type!r}")
                            continue
                        if effect_type in {"heal_hp", "damage"}:
                            amount = int(effect.get("amount", 0))
                            fraction = float(effect.get("fraction", 0.0)) if effect.get("fraction") is not None else 0.0
                            if amount <= 0 and fraction <= 0:
                                errors.append(f"item {item['id']}: {effect_type} needs amount or fraction")
                            if amount < 0 or amount > 5000:
                                errors.append(f"item {item['id']}: {effect_type} amount outside 0..5000")
                            if not 0 <= fraction <= 1:
                                errors.append(f"item {item['id']}: {effect_type} fraction outside 0..1")
                        elif effect_type in {"restore_mp", "restore_ap", "revive"}:
                            fraction = float(effect.get("fraction", -1))
                            if not 0 < fraction <= 1:
                                errors.append(f"item {item['id']}: {effect_type} fraction must be within 0..1")
                        elif effect_type == "cleanse":
                            statuses = effect.get("statuses") or []
                            for status_id in statuses:
                                if status_id not in harmful_statuses:
                                    errors.append(f"item {item['id']}: cleanse references non-harmful status {status_id!r}")
                            if not effect.get("all_harmful") and not statuses and int(effect.get("count", 0)) < 1:
                                errors.append(f"item {item['id']}: cleanse needs statuses, count, or all_harmful")
                        elif effect_type == "status":
                            status_id = effect.get("status")
                            if status_id not in valid_statuses:
                                errors.append(f"item {item['id']}: invalid status {status_id!r}")
                            turns = int(effect.get("turns", 0))
                            if not 1 <= turns <= 3:
                                errors.append(f"item {item['id']}: status turns must be within 1..3")

            for status_id in item.get("status_immune", []):
                if status_id not in harmful_statuses:
                    errors.append(f"item {item['id']}: invalid status immunity {status_id!r}")
            for status_id, amount in (item.get("status_resist") or {}).items():
                if status_id not in harmful_statuses:
                    errors.append(f"item {item['id']}: invalid status resistance {status_id!r}")
                try:
                    parsed = float(amount)
                except (TypeError, ValueError):
                    errors.append(f"item {item['id']}: status resistance must be numeric")
                else:
                    if not 0 <= parsed <= 1:
                        errors.append(f"item {item['id']}: status resistance outside 0..1")
            on_hit = item.get("on_hit_status")
            if on_hit is not None:
                if on_hit.get("status") not in valid_statuses:
                    errors.append(f"item {item['id']}: invalid on-hit status")
                chance(on_hit.get("chance", 0), f"item {item['id']} on-hit status")
                if not 1 <= int(on_hit.get("turns", 0)) <= 3:
                    errors.append(f"item {item['id']}: on-hit status turns must be within 1..3")
            lifesteal = float(item.get("lifesteal", 0.0))
            if not 0 <= lifesteal <= 0.25:
                errors.append(f"item {item['id']}: lifesteal outside 0..0.25")

        for monster in self.monsters.values():
            if int(monster.get("level", 0)) < 1:
                errors.append(f"monster {monster['id']}: level must be >= 1")
            if int(monster.get("hp", 0)) <= 0:
                errors.append(f"monster {monster['id']}: hp must be > 0")
            for stat in ("attack", "defense", "spirit", "xp", "jp", "gil"):
                if int(monster.get(stat, 0)) < 0:
                    errors.append(f"monster {monster['id']}: {stat} must be >= 0")
            special = monster.get("special") or {}
            if special:
                chance(special.get("chance", 0), f"monster {monster['id']} special")
                if float(special.get("multiplier", 0)) <= 0:
                    errors.append(f"monster {monster['id']}: special multiplier must be > 0")
            for drop in monster.get("drops", []):
                require(self.items, drop.get("item_id"), f"monster {monster['id']} drop")
                chance(drop.get("chance", 0), f"monster {monster['id']} drop")
                if int(drop.get("min", 1)) < 1 or int(drop.get("max", 1)) < int(drop.get("min", 1)):
                    errors.append(f"monster {monster['id']}: invalid drop quantity range")

        for boss in self.bosses.values():
            if int(boss.get("hp", 0)) <= 0:
                errors.append(f"boss {boss['id']}: hp must be > 0")
            if not 1 <= int(boss.get("recommended_level", 0)) <= 99:
                errors.append(f"boss {boss['id']}: recommended_level must be within 1..99")
            for reward in ("xp", "gil"):
                if int(boss.get(reward, 0)) < 0:
                    errors.append(f"boss {boss['id']}: {reward} must be >= 0")
            if int(boss.get("attacks_per_round", 1)) < 1:
                errors.append(f"boss {boss['id']}: attacks_per_round must be >= 1")
            if int(boss.get("aoe_every", 1)) < 1:
                errors.append(f"boss {boss['id']}: aoe_every must be >= 1")
            for drop in boss.get("drops", []):
                require(self.items, drop.get("item_id"), f"boss {boss['id']} drop")
                chance(drop.get("chance", 0), f"boss {boss['id']} drop")
            thresholds = [float(p.get("threshold", -1)) for p in boss.get("phases", [])]
            if thresholds and any(not 0 <= t <= 1 for t in thresholds):
                errors.append(f"boss {boss['id']}: phase threshold out of range")

        for hunt in self.hunts.values():
            require(self.monsters, hunt.get("monster_id"), f"hunt {hunt['id']}")
            require(self.items, hunt.get("first_clear_item"), f"hunt {hunt['id']} first-clear item")
            require(self.titles, hunt.get("first_clear_title"), f"hunt {hunt['id']} first-clear title")
            if hunt.get("rank") not in {"C", "B", "A", "S"}:
                errors.append(f"hunt {hunt['id']}: invalid rank")
            if int(hunt.get("min_level", 0)) < 1:
                errors.append(f"hunt {hunt['id']}: min_level must be >= 1")
            if int(hunt.get("cooldown_seconds", 0)) < 60:
                errors.append(f"hunt {hunt['id']}: cooldown must be >= 60 seconds")
            for reward, value in hunt.get("rewards", {}).items():
                if int(value) < 0:
                    errors.append(f"hunt {hunt['id']}: reward {reward} must be >= 0")

        for quest in self.quests.values():
            for req in quest.get("requirements", []):
                rtype = req.get("type")
                if rtype == "job_level":
                    require(self.jobs, req.get("job_id"), f"quest {quest['id']} requirement")
                elif rtype == "monster_kills":
                    require(self.monsters, req.get("monster_id"), f"quest {quest['id']} requirement")
                elif rtype == "hunt_clear":
                    require(self.hunts, req.get("hunt_id"), f"quest {quest['id']} requirement")
            rewards = quest.get("rewards", {})
            require(self.jobs, rewards.get("job"), f"quest {quest['id']} reward")
            require(self.titles, rewards.get("title"), f"quest {quest['id']} reward")

        for recipe in self.recipes.values():
            for material in recipe.get("materials", []):
                require(self.items, material.get("item_id"), f"recipe {recipe['id']} material")
            output = recipe.get("output", {})
            require(self.items, output.get("item_id"), f"recipe {recipe['id']} output")

        for relic in self.relics.values():
            require(self.jobs, relic.get("job_id"), f"relic {relic['id']} job")
            for stage in relic.get("stages", []):
                require(self.items, stage.get("reward_item"), f"relic {relic['id']} reward")
                for material in stage.get("cost", {}).get("items", []):
                    require(self.items, material.get("item_id"), f"relic {relic['id']} material")
                for req in stage.get("requirements", []):
                    if req.get("type") == "job_level":
                        require(self.jobs, req.get("job_id"), f"relic {relic['id']} requirement")
                    elif req.get("type") == "monster_kills":
                        require(self.monsters, req.get("monster_id"), f"relic {relic['id']} requirement")
                    elif req.get("type") == "hunt_clear":
                        require(self.hunts, req.get("hunt_id"), f"relic {relic['id']} requirement")

        for offer in self.seal_shop.values():
            require(self.items, offer.get("item_id"), f"seal shop {offer['id']}")
            if int(offer.get("quantity", 0)) < 1 or int(offer.get("cost", 0)) < 1:
                errors.append(f"seal shop {offer['id']}: quantity/cost must be positive")
        previous_forge = 0
        for tier in self.forge:
            level = int(tier.get("level", 0))
            if level != previous_forge + 1:
                errors.append("forge levels must be contiguous and start at +1")
            previous_forge = level
            if int(tier.get("gil", 0)) < 0:
                errors.append(f"forge +{level}: gil must be >= 0")
            bonus = float(tier.get("bonus_per_level", 0))
            if not 0 < bonus <= 0.50:
                errors.append(f"forge +{level}: bonus_per_level out of range")
            for material in tier.get("materials", []):
                require(self.items, material.get("item_id"), f"forge +{tier.get('level')}")
        valid_categories = {
            "Adventure", "Combat", "Bestiary", "Hunts", "Jobs", "Crafting",
            "Economy", "Relics", "Raids", "Social", "Comedy", "Boss", "Secret",
        }
        valid_tiers = {"bronze", "silver", "gold", "crystal"}
        for achievement in self.achievements.values():
            require(self.titles, achievement.get("reward_title"), f"achievement {achievement['id']} title")
            if achievement.get("category") not in valid_categories:
                errors.append(f"achievement {achievement['id']}: invalid category")
            if achievement.get("tier") not in valid_tiers:
                errors.append(f"achievement {achievement['id']}: invalid tier")
            if int(achievement.get("points", 0)) <= 0:
                errors.append(f"achievement {achievement['id']}: points must be > 0")
            cond = achievement.get("condition", {})
            if cond.get("type") in {"monster_kills", "monster_record_defeats"}:
                require(self.monsters, cond.get("monster_id"), f"achievement {achievement['id']}")
            if cond.get("type") == "boss_clear":
                require(self.bosses, cond.get("boss_id"), f"achievement {achievement['id']}")
            if cond.get("type") == "job_battles" and cond.get("job_id"):
                require(self.jobs, cond.get("job_id"), f"achievement {achievement['id']}")

        return errors

    def validate_or_raise(self) -> None:
        errors = self.validate()
        if errors:
            preview = "\n - ".join(errors[:25])
            more = f"\n... and {len(errors)-25} more" if len(errors) > 25 else ""
            raise ValueError(f"Game data validation failed:\n - {preview}{more}")

    def item(self, item_id: str | None) -> dict[str, Any] | None:
        if not item_id:
            return None
        return self.items.get(item_id)
