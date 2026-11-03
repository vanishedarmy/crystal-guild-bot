"""Narrative-only Expedition v2.0.1 scenes.

Every scene is deterministic for its run/stage/kind, generated from a dedicated
hash rather than the combat/economy RNG. It never changes timers, encounter
weights, resources, drops, or activity permissions.
"""
from __future__ import annotations

import hashlib


REGION_SCENES: dict[str, dict[str, tuple[str, ...]]] = {
    "emerald_wilds": {
        "arrival": ("Green light scatters through ancient boughs; the old trails are barely paths anymore.", "The forest hums with unseen life, and every rustle promises a story."),
        "travel": ("Beneath the emerald canopy, fallen stones mark a forgotten pilgrim road.", "A ribbon of sunlight finds its way through the towering roots.", "Your Chocobo pauses beside a moss-covered shrine and listens to the wind."),
        "combat": ("Something has been following the trail between the tree trunks.", "The forest falls silent just before a shadow breaks from the undergrowth."),
        "camp": ("Fireflies gather beyond the campfire, as though keeping watch.", "The forest settles around camp in a chorus of gentle, unfamiliar calls."),
        "return": ("The green roof finally opens, leaving the wilderness's secrets behind.", "The trail home seems shorter under the last warm light of the canopy."),
    },
    "ashen_highlands": {
        "arrival": ("Cinders drift across the high passes, where ruined furnaces still glow in the fog.", "A black volcanic ridge rises ahead; its silence feels borrowed."),
        "travel": ("Ash crunches underfoot beside the ribs of an abandoned Magitek hauler.", "A vent of orange steam whistles through cracked obsidian.", "Old hammer marks lead along a cliff toward a forge lost to the eruption."),
        "combat": ("A heavy scrape sounds from the other side of a smoking rockfall.", "The scorched path trembles as something emerges from the cinders."),
        "camp": ("The campfire is barely visible against the red glow of distant lava.", "Your party shelters between cold stones while molten rivers light the horizon."),
        "return": ("The sulfurous air lifts as the highlands fall behind you.", "One last ember flares on the ridge before the road bends home."),
    },
    "mistfen_marshes": {
        "arrival": ("A green-gray mist settles over the water; the marsh keeps its own map.", "Lantern lights wink between reeds, though no road leads to them."),
        "travel": ("A raised causeway vanishes into fog, then reappears somewhere unexpected.", "Bubbles rise around sunken stones engraved with worn runes.", "The reeds whisper in a voice almost like conversation."),
        "combat": ("A ripple crosses the black water against the current.", "Something shifts beneath the lilies; the fog refuses to part."),
        "camp": ("A ring of dry stones offers a rare place to rest above the marsh.", "Blue marshlights drift at the edge of camp but never approach."),
        "return": ("The fog thins and firm ground returns beneath your boots.", "Behind you, the marsh folds its hidden channels closed once more."),
    },
    "frostveil_reach": {
        "arrival": ("Frost settles on every strap as the white mountains rise ahead.", "Beyond the pass, a silver storm crawls slowly across the icefields."),
        "travel": ("Snow reveals the shape of a buried watchtower for a moment.", "Your tracks fill almost as quickly as you make them.", "Crystal-blue ice rings faintly beneath your feet."),
        "combat": ("A low growl rolls out from a drift that should be empty.", "The wind goes still; something is moving through the snow."),
        "camp": ("Warm light spills from the tent while the white world turns blue.", "The Chocobo tucks in its head as the fire pushes back the cold."),
        "return": ("The wind softens and the mountain road finally descends.", "The frozen peaks remain on the horizon like silent sentinels."),
    },
    "astral_scar": {
        "arrival": ("The earth opens into luminous fractures where starlight hangs at noon.", "Reality flickers along the scar; familiar constellations shine beneath your feet."),
        "travel": ("A broken bridge floats a handspan above its own shadow.", "Crystals chime in a rhythm no ordinary wind could make.", "The horizon bends around an ancient, impossible ruin."),
        "combat": ("The air warps, and a shape steps through a seam in the light.", "Your shadow moves first, warning of a presence in the rift."),
        "camp": ("A small circle of ordinary firelight anchors the strange night.", "Stars rearrange overhead while the party tries to sleep."),
        "return": ("The impossible glow retreats as the familiar sky returns.", "For a heartbeat, two roads home overlap before one becomes real."),
    },
    "shattered_sky_isles": {
        "arrival": ("The Guild Airship clears the cloudbank into a sea of drifting islands.", "The first floating cliffs appear like a fleet of stone ships."),
        "travel": ("Broken waterfalls pour into open sky and become silver mist.", "The hull passes close to a deserted sky-dock hung with old banners.", "An island turns slowly beneath the ship, its underside glittering with ore."),
        "combat": ("The lookout sounds the bell as a hostile silhouette rises from cloud cover.", "The deck tilts; something circles the ship just out of sight."),
        "camp": ("The engines idle beneath a bright constellation of floating islands.", "Crew lanterns sway as the Airship drifts into a sheltered current."),
        "return": ("The broken isles disappear beneath a closing blanket of cloud.", "The crew marks a safe passage through the drifting stone labyrinth."),
    },
    "aetherstorm_expanse": {
        "arrival": ("Aether lightning lights the cockpit in violet as the storm belt begins.", "The air tastes of ozone; the compass spins toward a cloud of living light."),
        "travel": ("Electric rivers crawl across the clouds below the Airship.", "The survey instruments sing as the hull slips through a charged corridor.", "A flash reveals the silhouette of a tower trapped inside a thunderhead."),
        "combat": ("A sudden bolt outlines something riding the storm toward the ship.", "The warning gauges flare as a shape dives out of charged vapor."),
        "camp": ("The crew anchors in a rare pocket of calm between storm walls.", "Blue sparks dance along the rail while the engines cool."),
        "return": ("The thunder fades to a distant rumble beyond the stern.", "The last static crackles away as clear skies reappear."),
    },
    "forgotten_dominion": {
        "arrival": ("A ruined empire floats beneath the Airship, its marble streets empty.", "Silent towers pierce the clouds, guarded by machines that forgot their masters."),
        "travel": ("The Airship glides above a plaza of enormous, motionless statues.", "A defense beacon blinks awake as the ship passes a crumbling arch.", "The old capital's clock towers still strike an hour nobody remembers."),
        "combat": ("Ancient sentry lights sweep across the deck.", "A metal guardian stirs within the silent city's broken defenses."),
        "camp": ("The crew watches the city glow softly through the night watch.", "A sheltered landing platform offers silence among the abandoned towers."),
        "return": ("The city's towers vanish into mist, their lights still burning.", "No one speaks until the last stone spire slips from view."),
    },
    "emberglass_caldera": {
        "arrival": ("Heat haze folds the sky above a vast ring of molten glass.", "The Airship enters a red-lit caldera where ash falls like snow."),
        "travel": ("Glass-black rock reflects the hull in a thousand broken facets.", "Cinder currents twist around the prow as the crew follows an old mining beacon.", "Below the clouds, a magma river illuminates the ruins of a buried foundry."),
        "combat": ("A roar rises through the heat, shaking ash from the railings.", "An ember-lit shape breaks through the smoke ahead."),
        "camp": ("Cooling engines tick in the shadow of a volcanic shelf.", "The night sky glows copper above the crew's temporary anchorage."),
        "return": ("The red light recedes and cool cloud air washes over the deck.", "Behind the ship, the caldera glows like a dying forge."),
    },
    "frostveil_observatory": {
        "arrival": ("An abandoned observatory hangs among pale stars and frozen cloud.", "The Airship approaches crystal domes that reflect unfamiliar constellations."),
        "travel": ("Frost etches a star chart across the observation glass.", "A ruined telescope points toward a moon that cannot be seen.", "The ship crosses a bridge of light between two icebound towers."),
        "combat": ("A crystalline chime rings out as something awakens in the white mist.", "The observatory's dark corridors suddenly answer with distant footsteps."),
        "camp": ("The crew rests beneath a silent dome of mirrored stars.", "Slow-moving auroras wash the anchored ship in violet light."),
        "return": ("The final crystal dome fades behind the cloud horizon.", "The navigator closes the star charts, still unable to explain one constellation."),
    },
    "gilded_mirage_expanse": {
        "arrival": ("Golden sand flows through the sky around cities that vanish when approached.", "The Airship enters a gleaming haze where horizons change without warning."),
        "travel": ("A palace appears on the horizon, then dissolves into sunlit dust.", "The compass points at an hourglass drifting among the clouds.", "Every window shows a different afternoon as the ship passes the mirage."),
        "combat": ("The sunlight fractures into a threatening silhouette.", "A reflection peels free of the air and rushes the ship."),
        "camp": ("The crew checks every watch twice before settling in for the night.", "Lanterns shine in two directions, though only one sun remains."),
        "return": ("The false horizons fall away and real stars guide the ship home.", "The crew returns with a map that looks slightly different at dusk."),
    },
}

_EVENT_ENDINGS: dict[str, tuple[str, ...]] = {
    "resource": ("A patient search reveals more than the terrain first promised.", "The land offers a small reward to those who know where to look."),
    "treasure": ("Someone has been here before; their forgotten belongings finally have a new keeper.", "The find hints at an older journey that ended long ago."),
    "hazard": ("The landscape reminds the party that caution is part of courage.", "The route demands a moment of steady nerves before it yields."),
    "discovery": ("This place was not on the Guild's charts yesterday.", "A new mark is inked onto the map before the moment can pass."),
    "traveler": ("A stranger's kindness proves more valuable than expected.", "News and goodwill travel even to the edge of the world."),
    "chocobo": ("Your companion spots a better path before anyone else can.", "A pleased whistle from your Chocobo breaks the tension."),
    "airship": ("The crew exchanges nervous looks, then returns to their stations.", "The navigator records the incident for the next flight."),
    "rare": ("The Guild archivists will want to hear every detail of this one.", "It is the sort of discovery that turns into a story back at the Guild."),
    "combat": ("The expedition's quiet is broken by the unmistakable sound of danger.", "Every member of the party knows the next moments will be decided in battle."),
    "event": ("Even an uneventful road keeps its small mysteries.", "Not every chapter of the journey needs a battle."),
}

_ROUTE_TONE = {
    "safe": ("The cautious path keeps to sheltered ground.", "A carefully chosen approach avoids the worst of the terrain."),
    "unknown": ("The road ahead is still a question mark.", "The next bend is absent from every chart."),
    "deep": ("The party ventures past the last familiar marker.", "The expedition presses into territory few have returned to describe."),
}


def scene(region_id: str, kind: str, run_id: str, stage: int = 1, route_id: str = "unknown") -> str:
    """Stable story for an Expedition state. Does not consume gameplay RNG."""
    region = REGION_SCENES.get(str(region_id))
    if not region:
        return ""
    stage = max(1, int(stage))
    key = f"{run_id}:{region_id}:{stage}:{route_id}:{kind}"
    value = int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big")

    if kind == "travel":
        travel = region["travel"][value % len(region["travel"])]
        route_lines = _ROUTE_TONE.get(route_id, _ROUTE_TONE["unknown"])
        return f"{travel} {route_lines[(value // 11) % len(route_lines)]}"
    if kind in region:
        rows = region[kind]
        return rows[value % len(rows)]
    endings = _EVENT_ENDINGS.get(kind, _EVENT_ENDINGS["event"])
    return endings[value % len(endings)]
