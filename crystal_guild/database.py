from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS players (
    twitch_id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    display_name TEXT NOT NULL,
    level INTEGER NOT NULL DEFAULT 1,
    xp INTEGER NOT NULL DEFAULT 0,
    gil INTEGER NOT NULL DEFAULT 250,
    hunt_seals INTEGER NOT NULL DEFAULT 0,
    current_job TEXT NOT NULL DEFAULT 'adventurer',
    current_region TEXT NOT NULL DEFAULT 'greenwind_plains',
    title TEXT NOT NULL DEFAULT 'Fresh Meat',
    stance TEXT NOT NULL DEFAULT 'balanced',
    ventures INTEGER NOT NULL DEFAULT 0,
    monsters_defeated INTEGER NOT NULL DEFAULT 0,
    deaths INTEGER NOT NULL DEFAULT 0,
    current_hp INTEGER NOT NULL DEFAULT 0,
    current_mp INTEGER,
    current_ap INTEGER,
    camp_until INTEGER NOT NULL DEFAULT 0,
    rests INTEGER NOT NULL DEFAULT 0,
    party_encounters INTEGER NOT NULL DEFAULT 0,
    raid_revives INTEGER NOT NULL DEFAULT 0,
    limit_breaks INTEGER NOT NULL DEFAULT 0,
    crafts INTEGER NOT NULL DEFAULT 0,
    forge_upgrades INTEGER NOT NULL DEFAULT 0,
    relics_completed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS player_jobs (
    player_id TEXT NOT NULL,
    job_id TEXT NOT NULL,
    level INTEGER NOT NULL DEFAULT 1,
    jp INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (player_id, job_id),
    FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS inventory (
    player_id TEXT NOT NULL,
    item_id TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (player_id, item_id),
    FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS equipment (
    player_id TEXT PRIMARY KEY,
    weapon_id TEXT,
    armor_id TEXT,
    accessory_id TEXT,
    FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS bestiary (
    player_id TEXT NOT NULL,
    monster_id TEXT NOT NULL,
    defeats INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (player_id, monster_id),
    FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS achievements (
    player_id TEXT NOT NULL,
    achievement_id TEXT NOT NULL,
    unlocked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (player_id, achievement_id),
    FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS player_hunts (
    player_id TEXT NOT NULL,
    hunt_id TEXT NOT NULL,
    clears INTEGER NOT NULL DEFAULT 0,
    first_cleared_at TEXT,
    last_cleared_at TEXT,
    PRIMARY KEY (player_id, hunt_id),
    FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS player_quests (
    player_id TEXT NOT NULL,
    quest_id TEXT NOT NULL,
    completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (player_id, quest_id),
    FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS player_titles (
    player_id TEXT NOT NULL,
    title_id TEXT NOT NULL,
    unlocked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (player_id, title_id),
    FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS mastery_slots (
    player_id TEXT NOT NULL,
    slot INTEGER NOT NULL,
    job_id TEXT NOT NULL,
    PRIMARY KEY (player_id, slot),
    FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS player_recipes (
    player_id TEXT NOT NULL,
    recipe_id TEXT NOT NULL,
    learned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (player_id, recipe_id),
    FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS item_upgrades (
    player_id TEXT NOT NULL,
    item_id TEXT NOT NULL,
    upgrade_level INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (player_id, item_id),
    FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS player_relics (
    player_id TEXT NOT NULL,
    relic_id TEXT NOT NULL,
    stage INTEGER NOT NULL DEFAULT 0,
    completed_at TEXT,
    PRIMARY KEY (player_id, relic_id),
    FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS drop_pity (
    player_id TEXT NOT NULL,
    pity_key TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (player_id, pity_key),
    FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cooldowns (
    player_id TEXT NOT NULL,
    action TEXT NOT NULL,
    available_at INTEGER NOT NULL,
    PRIMARY KEY (player_id, action),
    FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS player_shops (
    player_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    level_at_roll INTEGER NOT NULL,
    stock_json TEXT NOT NULL,
    generated_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,
    FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_player_shops_expires ON player_shops(expires_at);

CREATE TABLE IF NOT EXISTS player_boss_clears (
    player_id TEXT NOT NULL,
    boss_id TEXT NOT NULL,
    clears INTEGER NOT NULL DEFAULT 0,
    best_damage INTEGER NOT NULL DEFAULT 0,
    last_cleared_at TEXT,
    PRIMARY KEY (player_id, boss_id),
    FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_players_level ON players(level DESC);
CREATE INDEX IF NOT EXISTS idx_players_gil ON players(gil DESC);
CREATE INDEX IF NOT EXISTS idx_players_monsters ON players(monsters_defeated DESC);
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    asset_id TEXT NOT NULL,
    amount INTEGER NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_transactions_player_created ON transactions(player_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_kind_created ON transactions(kind, created_at DESC);

CREATE TABLE IF NOT EXISTS player_record_stats (
    player_id TEXT NOT NULL,
    metric TEXT NOT NULL,
    value INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (player_id, metric),
    FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS player_monster_records (
    player_id TEXT NOT NULL,
    monster_id TEXT NOT NULL,
    victories INTEGER NOT NULL DEFAULT 0,
    defeats INTEGER NOT NULL DEFAULT 0,
    damage_dealt INTEGER NOT NULL DEFAULT 0,
    damage_taken INTEGER NOT NULL DEFAULT 0,
    healing_done INTEGER NOT NULL DEFAULT 0,
    best_hit INTEGER NOT NULL DEFAULT 0,
    last_result TEXT,
    last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (player_id, monster_id),
    FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS player_job_records (
    player_id TEXT NOT NULL,
    job_id TEXT NOT NULL,
    battles INTEGER NOT NULL DEFAULT 0,
    victories INTEGER NOT NULL DEFAULT 0,
    damage_dealt INTEGER NOT NULL DEFAULT 0,
    healing_done INTEGER NOT NULL DEFAULT 0,
    boss_damage INTEGER NOT NULL DEFAULT 0,
    knockouts INTEGER NOT NULL DEFAULT 0,
    last_used_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (player_id, job_id),
    FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_record_stats_metric ON player_record_stats(metric, value DESC);
CREATE INDEX IF NOT EXISTS idx_monster_records_rivalry ON player_monster_records(player_id, defeats DESC);
CREATE INDEX IF NOT EXISTS idx_job_records_usage ON player_job_records(player_id, battles DESC);

-- Small authoritative runtime checkpoint. This stores live combat coordination
-- state plus bounded Portal-action replay receipts; player progression remains normalized above.
CREATE TABLE IF NOT EXISTS runtime_state (
    state_key TEXT PRIMARY KEY,
    value_json TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Sequential local database migrations. Version 1 represents the legacy
-- pre-migration Crystal Guild schema; version 2 adds persistent MP/AP;
-- version 3 adds additive Fellowship progression tables; version 4 adds
-- persistent Chocobo companion and registration-writ state; version 5 adds
-- persistent per-player Wayfarer Solo Expedition state; version 6 adds
-- persistent Chocobo portrait selection; version 7 adds durable Portal adventure result acknowledgements; version 8 adds
-- persistent v1.2 Expedition runs and per-region exploration progress; version 9 adds
-- persistent Fellowship Airship state, upgrades, mission participation, and mission history; version 10 adds
-- persistent per-player Dungeon runs and Dungeon clear/failure progress; version 11 adds
-- Gold Saucer accounts, persistent Mini Cactpot tickets, and play history; version 12 adds
-- persistent Gold Saucer Monster Toss game state; version 13 adds persistent Triple Triad collection, deck, records, and active match state; version 14 adds the personal Retainer Service and one persistent procurement assignment per player; version 15 adds targeted Retainer procurement history; version 16 adds authoritative per-player equipment Favorites for cross-device Portal sync; version 17 adds persistent Hero Mercenary contracts and contract history. Hotfix 3 expands the active contract table to one slot per Merc mission type while retaining schema version 17; version 18 adds permanent Merc recruitment records for expansion Heroes; version 19 adds the Fellowship Trading Post listing ledger.
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

DATABASE_SCHEMA_VERSION = 19


class Database:
    def __init__(self, path: str | Path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._closed = False
        self._tx_local = threading.local()
        self._tx_commits = 0
        self._tx_rollbacks = 0
        self._tx_savepoint_rollbacks = 0
        self.conn = sqlite3.connect(
            self.path,
            timeout=10.0,
            check_same_thread=False,
        )
        self.conn.row_factory = sqlite3.Row
        # Detect a legacy on-disk Guild before CREATE TABLE statements add the
        # migration ledger. This lets schema upgrades create a verified backup
        # before ALTER TABLE touches player data.
        self._preexisting_players_table = bool(
            self.conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='players'"
            ).fetchone()
        )
        self.pre_migration_backup_path: Path | None = None
        # WAL keeps readers responsive while the daemon writes encounter/raid
        # rewards. A single RLock still serializes this process's writes.
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA busy_timeout = 10000")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA synchronous = NORMAL")
        self.conn.execute("PRAGMA temp_store = MEMORY")
        self.conn.execute("PRAGMA cache_size = -16384")
        self.conn.execute("PRAGMA wal_autocheckpoint = 1000")
        self.conn.executescript(SCHEMA)
        self.conn.commit()
        self._run_schema_migrations()
        self._backfill_player_records()


    def _run_schema_migrations(self) -> None:
        """Apply sequential, idempotent local DB migrations in place.

        Existing pre-migration Guilds are treated as schema 1. Before the first
        structural change to a populated legacy database, a transactionally
        consistent SQLite backup is created and verified. Future migrations can
        append versions here without requiring players to hop through releases.
        """
        self.conn.execute(
            "INSERT OR IGNORE INTO schema_migrations(version,name) VALUES (1,'legacy_baseline')"
        )
        # Close the tiny metadata transaction before SQLite's backup API runs;
        # backup cannot progress while this same source connection owns an
        # uncommitted write transaction.
        self.conn.commit()
        columns = {str(row[1]) for row in self.conn.execute("PRAGMA table_info(players)").fetchall()}
        needs_v2 = "current_mp" not in columns or "current_ap" not in columns
        already_v2 = bool(
            self.conn.execute("SELECT 1 FROM schema_migrations WHERE version=2").fetchone()
        )

        if needs_v2 and self._preexisting_players_table:
            self.pre_migration_backup_path = self._verified_pre_migration_backup(2)

        if needs_v2:
            self.conn.execute("BEGIN IMMEDIATE")
            try:
                if "current_mp" not in columns:
                    self.conn.execute("ALTER TABLE players ADD COLUMN current_mp INTEGER")
                if "current_ap" not in columns:
                    self.conn.execute("ALTER TABLE players ADD COLUMN current_ap INTEGER")
                self.conn.execute(
                    "INSERT OR REPLACE INTO schema_migrations(version,name,applied_at) "
                    "VALUES (2,'persistent_mp_ap',CURRENT_TIMESTAMP)"
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise
        elif not already_v2:
            self.conn.execute(
                "INSERT INTO schema_migrations(version,name) VALUES (2,'persistent_mp_ap')"
            )
        self.conn.commit()

        already_v3 = bool(
            self.conn.execute("SELECT 1 FROM schema_migrations WHERE version=3").fetchone()
        )
        if not already_v3:
            if self._preexisting_players_table:
                self.pre_migration_backup_path = self._verified_pre_migration_backup(3)
            try:
                self.conn.executescript(
                    """
                    BEGIN IMMEDIATE;
                    CREATE TABLE IF NOT EXISTS fellowship_state (
                        singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
                        level INTEGER NOT NULL DEFAULT 1,
                        renown INTEGER NOT NULL DEFAULT 0,
                        active_project_id TEXT,
                        expedition_board_complete INTEGER NOT NULL DEFAULT 0,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS fellowship_members (
                        player_id TEXT PRIMARY KEY,
                        renown INTEGER NOT NULL DEFAULT 0,
                        founding_member INTEGER NOT NULL DEFAULT 0,
                        projects_contributed INTEGER NOT NULL DEFAULT 0,
                        gil_donated INTEGER NOT NULL DEFAULT 0,
                        materials_donated INTEGER NOT NULL DEFAULT 0,
                        orders_participated INTEGER NOT NULL DEFAULT 0,
                        deeds_assisted INTEGER NOT NULL DEFAULT 0,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
                    );
                    CREATE TABLE IF NOT EXISTS fellowship_facilities (
                        facility_id TEXT PRIMARY KEY,
                        tier INTEGER NOT NULL DEFAULT 0,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS fellowship_project_progress (
                        project_id TEXT NOT NULL,
                        requirement_key TEXT NOT NULL,
                        current INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY (project_id, requirement_key)
                    );
                    CREATE TABLE IF NOT EXISTS fellowship_project_members (
                        project_id TEXT NOT NULL,
                        player_id TEXT NOT NULL,
                        PRIMARY KEY (project_id, player_id),
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
                    );
                    CREATE TABLE IF NOT EXISTS fellowship_contributions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        player_id TEXT NOT NULL,
                        project_id TEXT NOT NULL,
                        kind TEXT NOT NULL,
                        asset_id TEXT NOT NULL,
                        amount INTEGER NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
                    );
                    CREATE INDEX IF NOT EXISTS idx_fellowship_contrib_recent
                    ON fellowship_contributions(created_at DESC);
                    CREATE TABLE IF NOT EXISTS fellowship_orders (
                        period_key TEXT NOT NULL,
                        order_id TEXT NOT NULL,
                        progress INTEGER NOT NULL DEFAULT 0,
                        target INTEGER NOT NULL,
                        completed_at TEXT,
                        PRIMARY KEY (period_key, order_id)
                    );
                    CREATE TABLE IF NOT EXISTS fellowship_order_members (
                        period_key TEXT NOT NULL,
                        order_id TEXT NOT NULL,
                        player_id TEXT NOT NULL,
                        PRIMARY KEY (period_key, order_id, player_id),
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
                    );
                    CREATE TABLE IF NOT EXISTS fellowship_deeds (
                        deed_id TEXT PRIMARY KEY,
                        progress INTEGER NOT NULL DEFAULT 0,
                        target INTEGER NOT NULL,
                        completed_at TEXT
                    );
                    CREATE TABLE IF NOT EXISTS fellowship_deed_members (
                        deed_id TEXT NOT NULL,
                        player_id TEXT NOT NULL,
                        PRIMARY KEY (deed_id, player_id),
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
                    );
                    CREATE TABLE IF NOT EXISTS fellowship_events (
                        event_key TEXT PRIMARY KEY,
                        player_id TEXT,
                        activity TEXT NOT NULL,
                        renown INTEGER NOT NULL DEFAULT 0,
                        amount INTEGER NOT NULL DEFAULT 1,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE SET NULL
                    );
                    CREATE TABLE IF NOT EXISTS fellowship_activity (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        player_id TEXT,
                        kind TEXT NOT NULL,
                        label TEXT NOT NULL,
                        amount INTEGER NOT NULL DEFAULT 0,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE SET NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_fellowship_activity_recent
                    ON fellowship_activity(created_at DESC);
                    """
                )
                self.conn.execute(
                    "INSERT OR IGNORE INTO fellowship_state(singleton_id,level,renown) VALUES (1,1,0)"
                )
                self.conn.execute(
                    "INSERT OR IGNORE INTO fellowship_facilities(facility_id,tier) VALUES ('guild_hall',1)"
                )
                for facility_id in ('infirmary','workshop','training_hall','archives','quartermaster'):
                    self.conn.execute(
                        "INSERT OR IGNORE INTO fellowship_facilities(facility_id,tier) VALUES (?,0)",
                        (facility_id,),
                    )
                if self._preexisting_players_table:
                    self.conn.execute(
                        "INSERT OR IGNORE INTO fellowship_members(player_id,founding_member) "
                        "SELECT twitch_id,1 FROM players"
                    )
                self.conn.execute(
                    "INSERT INTO schema_migrations(version,name) VALUES (3,'fellowship')"
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise
        already_v4 = bool(
            self.conn.execute("SELECT 1 FROM schema_migrations WHERE version=4").fetchone()
        )
        if not already_v4:
            if self._preexisting_players_table:
                self.pre_migration_backup_path = self._verified_pre_migration_backup(4)
            try:
                self.conn.executescript(
                    """
                    BEGIN IMMEDIATE;
                    CREATE TABLE IF NOT EXISTS player_chocobos (
                        player_id TEXT PRIMARY KEY,
                        name TEXT,
                        level INTEGER NOT NULL DEFAULT 1,
                        xp INTEGER NOT NULL DEFAULT 0,
                        writ_purchased_at INTEGER NOT NULL DEFAULT 0,
                        writ_ready_at INTEGER NOT NULL DEFAULT 0,
                        registered_at TEXT,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
                    );
                    CREATE TABLE IF NOT EXISTS player_chocobo_traits (
                        player_id TEXT NOT NULL,
                        trait_id TEXT NOT NULL,
                        unlocked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (player_id, trait_id),
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
                    );
                    CREATE INDEX IF NOT EXISTS idx_chocobos_level
                    ON player_chocobos(level DESC, xp DESC);
                    INSERT OR IGNORE INTO fellowship_facilities(facility_id,tier) VALUES ('chocobo_stable',0);
                    INSERT INTO schema_migrations(version,name) VALUES (4,'chocobo_companions');
                    COMMIT;
                    """
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise


        already_v5 = bool(
            self.conn.execute("SELECT 1 FROM schema_migrations WHERE version=5").fetchone()
        )
        if not already_v5:
            if self._preexisting_players_table:
                self.pre_migration_backup_path = self._verified_pre_migration_backup(5)
            try:
                self.conn.executescript(
                    """
                    BEGIN IMMEDIATE;
                    CREATE TABLE IF NOT EXISTS solo_expeditions (
                        player_id TEXT PRIMARY KEY,
                        state_json TEXT NOT NULL,
                        started_at INTEGER NOT NULL,
                        updated_at INTEGER NOT NULL,
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
                    );
                    CREATE INDEX IF NOT EXISTS idx_solo_expeditions_updated
                    ON solo_expeditions(updated_at DESC);
                    INSERT INTO schema_migrations(version,name) VALUES (5,'wayfarer_solo_expeditions');
                    COMMIT;
                    """
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

        already_v6 = bool(
            self.conn.execute("SELECT 1 FROM schema_migrations WHERE version=6").fetchone()
        )
        chocobo_columns = {str(row[1]) for row in self.conn.execute("PRAGMA table_info(player_chocobos)").fetchall()}
        if not already_v6:
            if self._preexisting_players_table:
                self.pre_migration_backup_path = self._verified_pre_migration_backup(6)
            self.conn.execute("BEGIN IMMEDIATE")
            try:
                if "portrait_id" not in chocobo_columns:
                    self.conn.execute(
                        "ALTER TABLE player_chocobos ADD COLUMN portrait_id TEXT NOT NULL DEFAULT 'classic_gold'"
                    )
                self.conn.execute(
                    "UPDATE player_chocobos SET portrait_id='classic_gold' "
                    "WHERE portrait_id IS NULL OR TRIM(portrait_id)=''"
                )
                self.conn.execute(
                    "INSERT OR REPLACE INTO schema_migrations(version,name,applied_at) "
                    "VALUES (6,'chocobo_portraits',CURRENT_TIMESTAMP)"
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

        already_v7 = bool(
            self.conn.execute("SELECT 1 FROM schema_migrations WHERE version=7").fetchone()
        )
        if not already_v7:
            if self._preexisting_players_table:
                self.pre_migration_backup_path = self._verified_pre_migration_backup(7)
            try:
                self.conn.executescript(
                    """
                    BEGIN IMMEDIATE;
                    CREATE TABLE IF NOT EXISTS portal_adventure_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        player_id TEXT NOT NULL,
                        kind TEXT NOT NULL,
                        result_json TEXT NOT NULL,
                        created_at INTEGER NOT NULL,
                        acknowledged_at INTEGER,
                        source_action_id TEXT,
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
                    );
                    CREATE INDEX IF NOT EXISTS idx_portal_adventure_results_pending
                    ON portal_adventure_results(player_id, acknowledged_at, created_at DESC, id DESC);
                    CREATE INDEX IF NOT EXISTS idx_portal_adventure_results_source
                    ON portal_adventure_results(source_action_id);
                    INSERT INTO schema_migrations(version,name) VALUES (7,'portal_adventure_result_inbox');
                    COMMIT;
                    """
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

        already_v8 = bool(
            self.conn.execute("SELECT 1 FROM schema_migrations WHERE version=8").fetchone()
        )
        if not already_v8:
            if self._preexisting_players_table:
                self.pre_migration_backup_path = self._verified_pre_migration_backup(8)
            try:
                self.conn.executescript(
                    """
                    BEGIN IMMEDIATE;
                    CREATE TABLE IF NOT EXISTS player_expeditions (
                        player_id TEXT PRIMARY KEY,
                        state_json TEXT NOT NULL,
                        started_at INTEGER NOT NULL,
                        updated_at INTEGER NOT NULL,
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
                    );
                    CREATE INDEX IF NOT EXISTS idx_player_expeditions_updated
                    ON player_expeditions(updated_at DESC);
                    CREATE TABLE IF NOT EXISTS player_region_exploration (
                        player_id TEXT NOT NULL,
                        region_id TEXT NOT NULL,
                        progress INTEGER NOT NULL DEFAULT 0,
                        stages_cleared INTEGER NOT NULL DEFAULT 0,
                        completed_runs INTEGER NOT NULL DEFAULT 0,
                        boss_clears INTEGER NOT NULL DEFAULT 0,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (player_id, region_id),
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
                    );
                    CREATE INDEX IF NOT EXISTS idx_region_exploration_progress
                    ON player_region_exploration(region_id, progress DESC);
                    INSERT INTO schema_migrations(version,name) VALUES (8,'expeditions_foundation');
                    COMMIT;
                    """
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

        already_v9 = bool(
            self.conn.execute("SELECT 1 FROM schema_migrations WHERE version=9").fetchone()
        )
        if not already_v9:
            if self._preexisting_players_table:
                self.pre_migration_backup_path = self._verified_pre_migration_backup(9)
            try:
                self.conn.executescript(
                    """
                    BEGIN IMMEDIATE;
                    CREATE TABLE IF NOT EXISTS fellowship_airship_state (
                        singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
                        built INTEGER NOT NULL DEFAULT 0,
                        active_mission_id TEXT,
                        active_run_id TEXT,
                        started_at INTEGER,
                        ends_at INTEGER,
                        progress INTEGER NOT NULL DEFAULT 0,
                        target INTEGER NOT NULL DEFAULT 0,
                        missions_completed INTEGER NOT NULL DEFAULT 0,
                        missions_failed INTEGER NOT NULL DEFAULT 0,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS fellowship_airship_upgrades (
                        upgrade_id TEXT PRIMARY KEY,
                        tier INTEGER NOT NULL DEFAULT 0,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS fellowship_airship_mission_members (
                        run_id TEXT NOT NULL,
                        player_id TEXT NOT NULL,
                        contribution INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY (run_id, player_id),
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
                    );
                    CREATE TABLE IF NOT EXISTS fellowship_airship_mission_history (
                        run_id TEXT PRIMARY KEY,
                        mission_id TEXT NOT NULL,
                        started_at INTEGER NOT NULL,
                        ended_at INTEGER NOT NULL,
                        outcome TEXT NOT NULL,
                        progress INTEGER NOT NULL DEFAULT 0,
                        target INTEGER NOT NULL DEFAULT 0,
                        guild_renown INTEGER NOT NULL DEFAULT 0,
                        participant_count INTEGER NOT NULL DEFAULT 0
                    );
                    CREATE INDEX IF NOT EXISTS idx_airship_mission_history_ended
                    ON fellowship_airship_mission_history(ended_at DESC);
                    INSERT OR IGNORE INTO fellowship_airship_state(singleton_id,built) VALUES (1,0);
                    INSERT OR IGNORE INTO fellowship_airship_upgrades(upgrade_id,tier) VALUES ('hull',0);
                    INSERT OR IGNORE INTO fellowship_airship_upgrades(upgrade_id,tier) VALUES ('engine',0);
                    INSERT OR IGNORE INTO fellowship_airship_upgrades(upgrade_id,tier) VALUES ('cargo',0);
                    INSERT OR IGNORE INTO fellowship_airship_upgrades(upgrade_id,tier) VALUES ('survey',0);
                    INSERT OR IGNORE INTO fellowship_airship_upgrades(upgrade_id,tier) VALUES ('crystal_core',0);
                    INSERT INTO schema_migrations(version,name) VALUES (9,'guild_airship');
                    COMMIT;
                    """
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

        already_v10 = bool(
            self.conn.execute("SELECT 1 FROM schema_migrations WHERE version=10").fetchone()
        )
        if not already_v10:
            if self._preexisting_players_table:
                self.pre_migration_backup_path = self._verified_pre_migration_backup(10)
            try:
                self.conn.executescript(
                    """
                    BEGIN IMMEDIATE;
                    CREATE TABLE IF NOT EXISTS player_dungeons (
                        player_id TEXT PRIMARY KEY,
                        state_json TEXT NOT NULL,
                        started_at INTEGER NOT NULL,
                        updated_at INTEGER NOT NULL,
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
                    );
                    CREATE INDEX IF NOT EXISTS idx_player_dungeons_updated
                    ON player_dungeons(updated_at DESC);
                    CREATE TABLE IF NOT EXISTS player_dungeon_progress (
                        player_id TEXT NOT NULL,
                        dungeon_id TEXT NOT NULL,
                        clears INTEGER NOT NULL DEFAULT 0,
                        defeats INTEGER NOT NULL DEFAULT 0,
                        retreats INTEGER NOT NULL DEFAULT 0,
                        best_rooms INTEGER NOT NULL DEFAULT 0,
                        last_outcome TEXT,
                        last_completed_at INTEGER,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (player_id, dungeon_id),
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
                    );
                    CREATE INDEX IF NOT EXISTS idx_dungeon_progress_clears
                    ON player_dungeon_progress(dungeon_id, clears DESC);
                    INSERT INTO schema_migrations(version,name) VALUES (10,'dungeons_foundation');
                    COMMIT;
                    """
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

        already_v11 = bool(
            self.conn.execute("SELECT 1 FROM schema_migrations WHERE version=11").fetchone()
        )
        if not already_v11:
            if self._preexisting_players_table:
                self.pre_migration_backup_path = self._verified_pre_migration_backup(11)
            try:
                self.conn.executescript(
                    """
                    BEGIN IMMEDIATE;
                    CREATE TABLE IF NOT EXISTS player_gold_saucer (
                        player_id TEXT PRIMARY KEY,
                        points INTEGER NOT NULL DEFAULT 0 CHECK(points >= 0),
                        lifetime_earned INTEGER NOT NULL DEFAULT 0 CHECK(lifetime_earned >= 0),
                        lifetime_spent INTEGER NOT NULL DEFAULT 0 CHECK(lifetime_spent >= 0),
                        cactpot_plays INTEGER NOT NULL DEFAULT 0 CHECK(cactpot_plays >= 0),
                        cactpot_wins INTEGER NOT NULL DEFAULT 0 CHECK(cactpot_wins >= 0),
                        cactpot_best_payout INTEGER NOT NULL DEFAULT 0 CHECK(cactpot_best_payout >= 0),
                        slots_spins INTEGER NOT NULL DEFAULT 0 CHECK(slots_spins >= 0),
                        slots_wins INTEGER NOT NULL DEFAULT 0 CHECK(slots_wins >= 0),
                        slots_best_payout INTEGER NOT NULL DEFAULT 0 CHECK(slots_best_payout >= 0),
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
                    );
                    CREATE TABLE IF NOT EXISTS gold_saucer_cactpot (
                        player_id TEXT PRIMARY KEY,
                        ticket_id TEXT NOT NULL,
                        state TEXT NOT NULL,
                        grid_json TEXT NOT NULL,
                        revealed_json TEXT NOT NULL,
                        chosen_line INTEGER,
                        payout INTEGER NOT NULL DEFAULT 0,
                        started_at INTEGER NOT NULL,
                        resolved_at INTEGER,
                        updated_at INTEGER NOT NULL,
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
                    );
                    CREATE TABLE IF NOT EXISTS gold_saucer_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        player_id TEXT NOT NULL,
                        game TEXT NOT NULL,
                        wager INTEGER NOT NULL DEFAULT 0,
                        payout INTEGER NOT NULL DEFAULT 0,
                        outcome TEXT NOT NULL,
                        details_json TEXT NOT NULL DEFAULT '{}',
                        created_at INTEGER NOT NULL,
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
                    );
                    CREATE INDEX IF NOT EXISTS idx_gold_saucer_history_player
                    ON gold_saucer_history(player_id, created_at DESC, id DESC);
                    INSERT INTO schema_migrations(version,name) VALUES (11,'gold_saucer_foundation');
                    COMMIT;
                    """
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

        already_v12 = bool(
            self.conn.execute("SELECT 1 FROM schema_migrations WHERE version=12").fetchone()
        )
        if not already_v12:
            if self._preexisting_players_table:
                self.pre_migration_backup_path = self._verified_pre_migration_backup(12)
            try:
                self.conn.executescript(
                    """
                    BEGIN IMMEDIATE;
                    CREATE TABLE IF NOT EXISTS gold_saucer_monster_toss (
                        player_id TEXT PRIMARY KEY,
                        game_id TEXT NOT NULL,
                        state TEXT NOT NULL,
                        throw_index INTEGER NOT NULL DEFAULT 0,
                        score INTEGER NOT NULL DEFAULT 0,
                        throws_json TEXT NOT NULL DEFAULT '[]',
                        started_at INTEGER NOT NULL,
                        resolved_at INTEGER,
                        updated_at INTEGER NOT NULL,
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
                    );
                    CREATE INDEX IF NOT EXISTS idx_gold_saucer_monster_toss_state
                    ON gold_saucer_monster_toss(state, updated_at DESC);
                    INSERT INTO schema_migrations(version,name) VALUES (12,'gold_saucer_monster_toss');
                    COMMIT;
                    """
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

        already_v13 = bool(
            self.conn.execute("SELECT 1 FROM schema_migrations WHERE version=13").fetchone()
        )
        if not already_v13:
            if self._preexisting_players_table:
                self.pre_migration_backup_path = self._verified_pre_migration_backup(13)
            try:
                self.conn.executescript(
                    """
                    BEGIN IMMEDIATE;
                    CREATE TABLE IF NOT EXISTS player_triple_triad (
                        player_id TEXT PRIMARY KEY,
                        collection_json TEXT NOT NULL DEFAULT '[]',
                        deck_json TEXT NOT NULL DEFAULT '[]',
                        matches INTEGER NOT NULL DEFAULT 0 CHECK(matches >= 0),
                        wins INTEGER NOT NULL DEFAULT 0 CHECK(wins >= 0),
                        draws INTEGER NOT NULL DEFAULT 0 CHECK(draws >= 0),
                        losses INTEGER NOT NULL DEFAULT 0 CHECK(losses >= 0),
                        cards_won INTEGER NOT NULL DEFAULT 0 CHECK(cards_won >= 0),
                        current_streak INTEGER NOT NULL DEFAULT 0 CHECK(current_streak >= 0),
                        best_streak INTEGER NOT NULL DEFAULT 0 CHECK(best_streak >= 0),
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
                    );
                    CREATE TABLE IF NOT EXISTS gold_saucer_triple_triad (
                        player_id TEXT PRIMARY KEY,
                        match_id TEXT NOT NULL,
                        state TEXT NOT NULL,
                        opponent_id TEXT NOT NULL,
                        board_json TEXT NOT NULL DEFAULT '[null,null,null,null,null,null,null,null,null]',
                        player_hand_json TEXT NOT NULL DEFAULT '[]',
                        npc_hand_json TEXT NOT NULL DEFAULT '[]',
                        turn TEXT NOT NULL DEFAULT 'player',
                        result TEXT,
                        started_at INTEGER NOT NULL,
                        resolved_at INTEGER,
                        updated_at INTEGER NOT NULL,
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
                    );
                    CREATE INDEX IF NOT EXISTS idx_gold_saucer_triple_triad_state
                    ON gold_saucer_triple_triad(state, updated_at DESC);
                    INSERT INTO schema_migrations(version,name) VALUES (13,'gold_saucer_triple_triad');
                    COMMIT;
                    """
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

        already_v14 = bool(
            self.conn.execute("SELECT 1 FROM schema_migrations WHERE version=14").fetchone()
        )
        if not already_v14:
            if self._preexisting_players_table:
                self.pre_migration_backup_path = self._verified_pre_migration_backup(14)
            try:
                self.conn.executescript(
                    """
                    BEGIN IMMEDIATE;
                    CREATE TABLE IF NOT EXISTS player_retainers (
                        player_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL DEFAULT 'Guild Retainer',
                        xp INTEGER NOT NULL DEFAULT 0 CHECK(xp >= 0),
                        assignments_completed INTEGER NOT NULL DEFAULT 0 CHECK(assignments_completed >= 0),
                        materials_found INTEGER NOT NULL DEFAULT 0 CHECK(materials_found >= 0),
                        bonus_finds INTEGER NOT NULL DEFAULT 0 CHECK(bonus_finds >= 0),
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
                    );
                    CREATE TABLE IF NOT EXISTS retainer_assignments (
                        player_id TEXT PRIMARY KEY,
                        assignment_id TEXT NOT NULL,
                        assignment_type TEXT NOT NULL,
                        state TEXT NOT NULL,
                        cost_gil INTEGER NOT NULL CHECK(cost_gil >= 0),
                        reward_json TEXT NOT NULL DEFAULT '{}',
                        dispatched_at INTEGER NOT NULL,
                        ready_at INTEGER NOT NULL,
                        collected_at INTEGER,
                        updated_at INTEGER NOT NULL,
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
                    );
                    CREATE INDEX IF NOT EXISTS idx_retainer_assignments_state
                    ON retainer_assignments(state, ready_at);
                    INSERT INTO schema_migrations(version,name) VALUES (14,'retainer_service');
                    COMMIT;
                    """
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise


        already_v15 = bool(
            self.conn.execute("SELECT 1 FROM schema_migrations WHERE version=15").fetchone()
        )
        if not already_v15:
            if self._preexisting_players_table:
                self.pre_migration_backup_path = self._verified_pre_migration_backup(15)
            try:
                self.conn.executescript(
                    """
                    BEGIN IMMEDIATE;
                    CREATE TABLE IF NOT EXISTS retainer_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        player_id TEXT NOT NULL,
                        assignment_id TEXT NOT NULL UNIQUE,
                        assignment_type TEXT NOT NULL,
                        priority_item_id TEXT,
                        cost_gil INTEGER NOT NULL CHECK(cost_gil >= 0),
                        reward_json TEXT NOT NULL DEFAULT '{}',
                        retainer_xp INTEGER NOT NULL DEFAULT 0 CHECK(retainer_xp >= 0),
                        collected_at INTEGER NOT NULL,
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
                    );
                    CREATE INDEX IF NOT EXISTS idx_retainer_history_player_collected
                    ON retainer_history(player_id, collected_at DESC, id DESC);
                    INSERT INTO schema_migrations(version,name) VALUES (15,'retainer_targeted_procurement');
                    COMMIT;
                    """
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

        already_v16 = bool(
            self.conn.execute("SELECT 1 FROM schema_migrations WHERE version=16").fetchone()
        )
        if not already_v16:
            if self._preexisting_players_table:
                self.pre_migration_backup_path = self._verified_pre_migration_backup(16)
            try:
                self.conn.executescript(
                    """
                    BEGIN IMMEDIATE;
                    CREATE TABLE IF NOT EXISTS player_gear_favorites (
                        player_id TEXT NOT NULL,
                        item_id TEXT NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (player_id, item_id),
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
                    );
                    CREATE INDEX IF NOT EXISTS idx_player_gear_favorites_player
                    ON player_gear_favorites(player_id, created_at, item_id);
                    INSERT INTO schema_migrations(version,name) VALUES (16,'cross_device_gear_favorites');
                    COMMIT;
                    """
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

        already_v17 = bool(
            self.conn.execute("SELECT 1 FROM schema_migrations WHERE version=17").fetchone()
        )
        if not already_v17:
            if self._preexisting_players_table:
                self.pre_migration_backup_path = self._verified_pre_migration_backup(17)
            try:
                self.conn.executescript(
                    """
                    BEGIN IMMEDIATE;
                    CREATE TABLE IF NOT EXISTS player_merc_contracts (
                        player_id TEXT NOT NULL,
                        hero_id TEXT NOT NULL,
                        mission_type TEXT NOT NULL,
                        fee_marks INTEGER NOT NULL CHECK(fee_marks >= 0),
                        hired_at INTEGER NOT NULL,
                        updated_at INTEGER NOT NULL,
                        PRIMARY KEY (player_id, mission_type),
                        UNIQUE (player_id, hero_id),
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
                    );
                    CREATE TABLE IF NOT EXISTS merc_contract_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        player_id TEXT NOT NULL,
                        hero_id TEXT NOT NULL,
                        mission_type TEXT NOT NULL,
                        fee_marks INTEGER NOT NULL CHECK(fee_marks >= 0),
                        outcome TEXT NOT NULL,
                        contracted_at INTEGER NOT NULL,
                        consumed_at INTEGER NOT NULL,
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
                    );
                    CREATE INDEX IF NOT EXISTS idx_merc_history_player
                    ON merc_contract_history(player_id, consumed_at DESC, id DESC);
                    INSERT INTO schema_migrations(version,name) VALUES (17,'hero_merc_service');
                    COMMIT;
                    """
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

        # Hotfix 3: early v1.8 Alpha 1 schema-17 databases stored only one
        # Merc contract per player (player_id was the sole primary key). The
        # feature now supports one independent Hunt, Venture, and Raid slot.
        # Repair that table layout in-place while preserving any active row.
        merc_info = self.conn.execute("PRAGMA table_info(player_merc_contracts)").fetchall()
        merc_pk = [str(row["name"]) for row in sorted(merc_info, key=lambda row: int(row["pk"] or 0)) if int(row["pk"] or 0) > 0]
        if merc_info and merc_pk == ["player_id"]:
            try:
                self.conn.executescript(
                    """
                    BEGIN IMMEDIATE;
                    ALTER TABLE player_merc_contracts RENAME TO player_merc_contracts_single_slot;
                    CREATE TABLE player_merc_contracts (
                        player_id TEXT NOT NULL,
                        hero_id TEXT NOT NULL,
                        mission_type TEXT NOT NULL,
                        fee_marks INTEGER NOT NULL CHECK(fee_marks >= 0),
                        hired_at INTEGER NOT NULL,
                        updated_at INTEGER NOT NULL,
                        PRIMARY KEY (player_id, mission_type),
                        UNIQUE (player_id, hero_id),
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
                    );
                    INSERT INTO player_merc_contracts(player_id,hero_id,mission_type,fee_marks,hired_at,updated_at)
                    SELECT player_id,hero_id,mission_type,fee_marks,hired_at,updated_at
                    FROM player_merc_contracts_single_slot;
                    DROP TABLE player_merc_contracts_single_slot;
                    COMMIT;
                    """
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

        already_v18 = bool(
            self.conn.execute("SELECT 1 FROM schema_migrations WHERE version=18").fetchone()
        )
        if not already_v18:
            if self._preexisting_players_table:
                self.pre_migration_backup_path = self._verified_pre_migration_backup(18)
            try:
                self.conn.executescript(
                    """
                    BEGIN IMMEDIATE;
                    CREATE TABLE IF NOT EXISTS player_merc_recruits (
                        player_id TEXT NOT NULL,
                        hero_id TEXT NOT NULL,
                        unlock_method TEXT NOT NULL,
                        gil_paid INTEGER NOT NULL DEFAULT 0 CHECK(gil_paid >= 0),
                        recruited_at INTEGER NOT NULL,
                        PRIMARY KEY (player_id, hero_id),
                        FOREIGN KEY (player_id) REFERENCES players(twitch_id) ON DELETE CASCADE
                    );
                    CREATE INDEX IF NOT EXISTS idx_merc_recruits_player
                    ON player_merc_recruits(player_id, recruited_at, hero_id);
                    INSERT INTO schema_migrations(version,name) VALUES (18,'merc_recruitment');
                    COMMIT;
                    """
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

        already_v19 = bool(
            self.conn.execute("SELECT 1 FROM schema_migrations WHERE version=19").fetchone()
        )
        if not already_v19:
            if self._preexisting_players_table:
                self.pre_migration_backup_path = self._verified_pre_migration_backup(19)
            try:
                self.conn.executescript(
                    """
                    BEGIN IMMEDIATE;
                    CREATE TABLE IF NOT EXISTS trading_post_listings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        seller_id TEXT NOT NULL,
                        item_id TEXT NOT NULL,
                        quantity INTEGER NOT NULL CHECK(quantity > 0),
                        unit_price INTEGER NOT NULL CHECK(unit_price > 0),
                        listing_fee INTEGER NOT NULL DEFAULT 0 CHECK(listing_fee >= 0),
                        status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','sold','cancelled','expired')),
                        created_at INTEGER NOT NULL,
                        expires_at INTEGER NOT NULL,
                        buyer_id TEXT,
                        sold_at INTEGER,
                        payout_gil INTEGER NOT NULL DEFAULT 0 CHECK(payout_gil >= 0),
                        tax_gil INTEGER NOT NULL DEFAULT 0 CHECK(tax_gil >= 0),
                        FOREIGN KEY (seller_id) REFERENCES players(twitch_id) ON DELETE CASCADE,
                        FOREIGN KEY (buyer_id) REFERENCES players(twitch_id) ON DELETE SET NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_trading_post_active
                    ON trading_post_listings(status, expires_at, created_at DESC, id DESC);
                    CREATE INDEX IF NOT EXISTS idx_trading_post_seller
                    ON trading_post_listings(seller_id, created_at DESC, id DESC);
                    CREATE INDEX IF NOT EXISTS idx_trading_post_item
                    ON trading_post_listings(item_id, status, unit_price, created_at DESC);
                    INSERT INTO schema_migrations(version,name) VALUES (19,'fellowship_trading_post');
                    COMMIT;
                    """
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

        # INSERT OR IGNORE for the baseline opens a transaction even when no
        # structural migration is necessary; always close it before normal
        # database helpers begin their own composable transactions.
        self.conn.commit()

    def _verified_pre_migration_backup(self, target_version: int) -> Path | None:
        """Create and verify an automatic backup before a schema migration."""
        if self.path == ":memory:":
            return None
        source = Path(self.path)
        if not source.exists():
            return None
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        target = source.parent / "backups" / f"pre_schema_{target_version}_{stamp}.db"
        saved = self.backup(target)
        verify = sqlite3.connect(saved, timeout=10.0)
        try:
            quick = str(verify.execute("PRAGMA quick_check").fetchone()[0])
            if quick.lower() != "ok":
                raise RuntimeError(f"Pre-migration backup failed quick_check: {quick}")
            backup_players = int(verify.execute("SELECT COUNT(*) FROM players").fetchone()[0])
            live_players = int(self.conn.execute("SELECT COUNT(*) FROM players").fetchone()[0])
            if backup_players != live_players:
                raise RuntimeError(
                    f"Pre-migration backup player-count mismatch: {backup_players} != {live_players}"
                )
        finally:
            verify.close()
        return saved

    def schema_version(self) -> int:
        row = self.one("SELECT COALESCE(MAX(version),1) AS version FROM schema_migrations")
        return int(row["version"]) if row else 1

    def _backfill_player_records(self) -> None:
        legacy = {
            "ventures_started": "ventures",
            "monsters_defeated": "monsters_defeated",
            "times_ko": "deaths",
            "camp_rests": "rests",
            "party_encounters": "party_encounters",
            "raid_revives": "raid_revives",
            "limit_breaks": "limit_breaks",
            "crafts": "crafts",
            "forge_upgrades": "forge_upgrades",
            "relics_completed": "relics_completed",
        }
        with self.tx() as conn:
            for metric, column in legacy.items():
                conn.execute(
                    f"""
                    INSERT OR IGNORE INTO player_record_stats(player_id, metric, value)
                    SELECT twitch_id, ?, {column} FROM players
                    """,
                    (metric,),
                )
            derived = {
                "gil_earned": ("gil", ">", 0),
                "gil_spent": ("gil", "<", 0),
                "items_acquired": ("item", ">", 0),
                "items_spent": ("item", "<", 0),
                "hunt_seals_earned": ("hunt_seals", ">", 0),
                "hunt_seals_spent": ("hunt_seals", "<", 0),
            }
            for metric, (kind, op, zero) in derived.items():
                amount = "SUM(amount)" if op == ">" else "-SUM(amount)"
                conn.execute(
                    f"""
                    INSERT OR IGNORE INTO player_record_stats(player_id, metric, value)
                    SELECT player_id, ?, COALESCE({amount}, 0)
                    FROM transactions
                    WHERE kind=? AND amount {op} ?
                    GROUP BY player_id
                    """,
                    (metric, kind, zero),
                )
            conn.execute(
                """
                INSERT OR IGNORE INTO player_record_stats(player_id, metric, value)
                SELECT player_id, 'hunt_clears', COALESCE(SUM(clears), 0)
                FROM player_hunts GROUP BY player_id
                """
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO player_record_stats(player_id, metric, value)
                SELECT player_id, 'boss_clears', COALESCE(SUM(clears), 0)
                FROM player_boss_clears GROUP BY player_id
                """
            )

    def update_record_stats(
        self,
        player_id: str,
        increments: dict[str, int] | None = None,
        maxima: dict[str, int] | None = None,
    ) -> None:
        increments = {key: int(value) for key, value in (increments or {}).items() if int(value)}
        maxima = {key: int(value) for key, value in (maxima or {}).items()}
        if not increments and not maxima:
            return
        with self.tx() as conn:
            for metric, amount in increments.items():
                conn.execute(
                    """
                    INSERT INTO player_record_stats(player_id, metric, value) VALUES (?, ?, ?)
                    ON CONFLICT(player_id, metric) DO UPDATE SET
                        value=player_record_stats.value+excluded.value,
                        updated_at=CURRENT_TIMESTAMP
                    """,
                    (player_id, metric, amount),
                )
            for metric, value in maxima.items():
                conn.execute(
                    """
                    INSERT INTO player_record_stats(player_id, metric, value) VALUES (?, ?, ?)
                    ON CONFLICT(player_id, metric) DO UPDATE SET
                        value=MAX(player_record_stats.value, excluded.value),
                        updated_at=CURRENT_TIMESTAMP
                    """,
                    (player_id, metric, value),
                )

    def add_record_stat(self, player_id: str, metric: str, amount: int = 1) -> None:
        if not amount:
            return
        with self.tx() as conn:
            conn.execute(
                """
                INSERT INTO player_record_stats(player_id, metric, value) VALUES (?, ?, ?)
                ON CONFLICT(player_id, metric) DO UPDATE SET
                    value=player_record_stats.value+excluded.value,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (player_id, metric, int(amount)),
            )

    def max_record_stat(self, player_id: str, metric: str, value: int) -> None:
        with self.tx() as conn:
            conn.execute(
                """
                INSERT INTO player_record_stats(player_id, metric, value) VALUES (?, ?, ?)
                ON CONFLICT(player_id, metric) DO UPDATE SET
                    value=MAX(player_record_stats.value, excluded.value),
                    updated_at=CURRENT_TIMESTAMP
                """,
                (player_id, metric, int(value)),
            )

    def min_record_stat(self, player_id: str, metric: str, value: int) -> None:
        """Persist a positive personal-best metric where lower is better."""
        value = int(value)
        if value <= 0:
            return
        with self.tx() as conn:
            conn.execute(
                """
                INSERT INTO player_record_stats(player_id, metric, value) VALUES (?, ?, ?)
                ON CONFLICT(player_id, metric) DO UPDATE SET
                    value=MIN(player_record_stats.value, excluded.value),
                    updated_at=CURRENT_TIMESTAMP
                """,
                (player_id, metric, value),
            )

    def record_monster_result(
        self,
        player_id: str,
        monster_id: str,
        *,
        won: bool,
        knocked_out: bool = False,
        damage_dealt: int = 0,
        damage_taken: int = 0,
        healing_done: int = 0,
        best_hit: int = 0,
    ) -> None:
        victories = 1 if won else 0
        defeats = 1 if knocked_out or not won else 0
        with self.tx() as conn:
            conn.execute(
                """
                INSERT INTO player_monster_records(
                    player_id, monster_id, victories, defeats, damage_dealt,
                    damage_taken, healing_done, best_hit, last_result
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(player_id, monster_id) DO UPDATE SET
                    victories=player_monster_records.victories+excluded.victories,
                    defeats=player_monster_records.defeats+excluded.defeats,
                    damage_dealt=player_monster_records.damage_dealt+excluded.damage_dealt,
                    damage_taken=player_monster_records.damage_taken+excluded.damage_taken,
                    healing_done=player_monster_records.healing_done+excluded.healing_done,
                    best_hit=MAX(player_monster_records.best_hit, excluded.best_hit),
                    last_result=excluded.last_result,
                    last_seen_at=CURRENT_TIMESTAMP
                """,
                (
                    player_id, monster_id, victories, defeats, int(damage_dealt),
                    int(damage_taken), int(healing_done), int(best_hit),
                    "victory" if won else "defeat",
                ),
            )

    def record_job_battle(
        self,
        player_id: str,
        job_id: str,
        *,
        won: bool,
        knocked_out: bool = False,
        damage_dealt: int = 0,
        healing_done: int = 0,
        boss_damage: int = 0,
    ) -> None:
        with self.tx() as conn:
            conn.execute(
                """
                INSERT INTO player_job_records(
                    player_id, job_id, battles, victories, damage_dealt,
                    healing_done, boss_damage, knockouts
                ) VALUES (?, ?, 1, ?, ?, ?, ?, ?)
                ON CONFLICT(player_id, job_id) DO UPDATE SET
                    battles=player_job_records.battles+1,
                    victories=player_job_records.victories+excluded.victories,
                    damage_dealt=player_job_records.damage_dealt+excluded.damage_dealt,
                    healing_done=player_job_records.healing_done+excluded.healing_done,
                    boss_damage=player_job_records.boss_damage+excluded.boss_damage,
                    knockouts=player_job_records.knockouts+excluded.knockouts,
                    last_used_at=CURRENT_TIMESTAMP
                """,
                (
                    player_id, job_id, 1 if won else 0, int(damage_dealt),
                    int(healing_done), int(boss_damage), 1 if knocked_out else 0,
                ),
            )

    @contextmanager
    def tx(self, *, immediate: bool = False) -> Iterator[sqlite3.Connection]:
        """Open a composable SQLite transaction.

        Nested write helpers are atomic. The outermost scope
        owns COMMIT/ROLLBACK; inner scopes use SAVEPOINTs so a helper can fail
        without accidentally committing the caller's larger game operation.
        ``immediate=True`` acquires SQLite write intent before the first read,
        which lets cross-connection authoritative state guards serialize stale
        state checks before any gameplay mutation is evaluated.
        """
        with self._lock:
            if self._closed:
                raise RuntimeError("Database connection is closed.")
            depth = int(getattr(self._tx_local, "depth", 0))
            outermost = depth == 0
            savepoint = f"cg_sp_{threading.get_ident()}_{depth}"
            if outermost:
                self.conn.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
            else:
                self.conn.execute(f"SAVEPOINT {savepoint}")
            self._tx_local.depth = depth + 1
            try:
                yield self.conn
                if outermost:
                    self.conn.commit()
                    self._tx_commits += 1
                else:
                    self.conn.execute(f"RELEASE SAVEPOINT {savepoint}")
            except Exception:
                if outermost:
                    self.conn.rollback()
                    self._tx_rollbacks += 1
                else:
                    self.conn.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
                    self.conn.execute(f"RELEASE SAVEPOINT {savepoint}")
                    self._tx_savepoint_rollbacks += 1
                raise
            finally:
                self._tx_local.depth = depth

    def runtime_state(self, key: str) -> sqlite3.Row | None:
        return self.one(
            "SELECT state_key, value_json, updated_at FROM runtime_state WHERE state_key=?",
            (str(key),),
        )

    def set_runtime_state(self, key: str, value_json: str) -> None:
        with self.tx() as conn:
            conn.execute(
                """
                INSERT INTO runtime_state(state_key, value_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(state_key) DO UPDATE SET
                    value_json=excluded.value_json,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (str(key), str(value_json)),
            )

    def delete_runtime_state(self, key: str) -> None:
        self.execute("DELETE FROM runtime_state WHERE state_key=?", (str(key),))

    def transaction_stats(self) -> dict[str, int]:
        with self._lock:
            return {
                "depth": int(getattr(self._tx_local, "depth", 0)),
                "commits": int(self._tx_commits),
                "rollbacks": int(self._tx_rollbacks),
                "savepoint_rollbacks": int(self._tx_savepoint_rollbacks),
            }

    def economy_snapshot(self, days: int = 7) -> dict[str, object]:
        """Return a compact authoritative gil source/sink pulse.

        The ledger is already the source of truth for player Records. Gold
        Saucer reuses it for owner diagnostics rather than creating a second
        accounting system. Source IDs are grouped by their prefix (monster,
        hunt, boss, shop, craft, forge, relic, daily, sell, ...).
        """
        window = max(1, min(90, int(days)))
        since = f"-{window} days"
        with self._lock:
            players_row = self.conn.execute(
                "SELECT COUNT(*) AS players, COALESCE(SUM(gil),0) AS circulating FROM players"
            ).fetchone()
            totals = self.conn.execute(
                """
                SELECT
                    COUNT(*) AS tx_count,
                    COALESCE(SUM(CASE WHEN amount>0 THEN amount ELSE 0 END),0) AS earned,
                    COALESCE(-SUM(CASE WHEN amount<0 THEN amount ELSE 0 END),0) AS spent
                FROM transactions
                WHERE kind='gil' AND created_at >= datetime('now', ?)
                """,
                (since,),
            ).fetchone()
            rows = self.conn.execute(
                """
                SELECT source, SUM(amount) AS amount
                FROM transactions
                WHERE kind='gil' AND created_at >= datetime('now', ?)
                GROUP BY source
                """,
                (since,),
            ).fetchall()

        earned_by: dict[str, int] = {}
        spent_by: dict[str, int] = {}
        for row in rows:
            source = str(row["source"] or "unknown")
            family = source.split(":", 1)[0] or "unknown"
            amount = int(row["amount"] or 0)
            if amount > 0:
                earned_by[family] = earned_by.get(family, 0) + amount
            elif amount < 0:
                spent_by[family] = spent_by.get(family, 0) + abs(amount)

        top_source = max(earned_by.items(), key=lambda item: item[1], default=None)
        top_sink = max(spent_by.items(), key=lambda item: item[1], default=None)
        return {
            "days": window,
            "players": int(players_row["players"] or 0),
            "circulating_gil": int(players_row["circulating"] or 0),
            "earned": int(totals["earned"] or 0),
            "spent": int(totals["spent"] or 0),
            "transactions": int(totals["tx_count"] or 0),
            "top_source": top_source,
            "top_sink": top_sink,
            "earned_by_source": earned_by,
            "spent_by_source": spent_by,
        }

    def one(self, sql: str, params: tuple = ()) -> sqlite3.Row | None:
        with self._lock:
            return self.conn.execute(sql, params).fetchone()

    def all(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            return list(self.conn.execute(sql, params).fetchall())

    def execute(self, sql: str, params: tuple = ()) -> None:
        with self.tx() as conn:
            conn.execute(sql, params)

    def health_check(self) -> bool:
        with self._lock:
            if self._closed:
                return False
            row = self.conn.execute("SELECT 1").fetchone()
            return bool(row and row[0] == 1)

    def quick_check(self) -> list[str]:
        """Return SQLite quick-check results; an empty list means healthy."""
        with self._lock:
            if self._closed:
                return ["database connection is closed"]
            rows = self.conn.execute("PRAGMA quick_check").fetchall()
            messages = [str(row[0]) for row in rows]
            return [] if messages == ["ok"] else messages

    def integrity_report(self) -> dict[str, object]:
        """Return release-readiness diagnostics without mutating data.

        ``quick_check`` catches SQLite page/index corruption while
        ``foreign_key_check`` catches orphaned progression rows. The PRAGMA
        values make it easy to verify that the live database still has the
        concurrency settings Crystal Guild expects after an upgrade.
        """
        with self._lock:
            if self._closed:
                return {
                    "ok": False,
                    "quick_check": ["database connection is closed"],
                    "foreign_key_violations": ["database connection is closed"],
                    "journal_mode": "closed",
                    "synchronous": -1,
                    "busy_timeout_ms": 0,
                    "players": 0,
                    "transactions": 0,
                }
            quick_rows = self.conn.execute("PRAGMA quick_check").fetchall()
            quick_messages = [str(row[0]) for row in quick_rows]
            quick_failures = [] if quick_messages == ["ok"] else quick_messages
            fk_rows = self.conn.execute("PRAGMA foreign_key_check").fetchall()
            fk_failures = [
                f"{row[0]} rowid={row[1]} parent={row[2]} fk={row[3]}" for row in fk_rows
            ]
            journal_mode = str(self.conn.execute("PRAGMA journal_mode").fetchone()[0]).lower()
            synchronous = int(self.conn.execute("PRAGMA synchronous").fetchone()[0])
            busy_timeout = int(self.conn.execute("PRAGMA busy_timeout").fetchone()[0])
            players = int(self.conn.execute("SELECT COUNT(*) FROM players").fetchone()[0])
            transactions = int(self.conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0])
            return {
                "ok": not quick_failures and not fk_failures and journal_mode == "wal" and busy_timeout >= 1000,
                "quick_check": quick_failures,
                "foreign_key_violations": fk_failures,
                "journal_mode": journal_mode,
                "synchronous": synchronous,
                "busy_timeout_ms": busy_timeout,
                "players": players,
                "transactions": transactions,
            }

    def backup(self, destination: str | Path) -> Path:
        """Create a transactionally consistent SQLite backup, including WAL data."""
        target = Path(destination).resolve()
        source = Path(self.path).resolve()
        if target == source:
            raise ValueError("Backup destination must differ from the live database path.")
        target.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            if self._closed:
                raise RuntimeError("Cannot back up a closed database.")
            backup_conn = sqlite3.connect(target, timeout=10.0)
            try:
                self.conn.backup(backup_conn)
                backup_conn.commit()
            finally:
                backup_conn.close()
        return target

    def optimize(self) -> None:
        with self._lock:
            if self._closed:
                return
            self.conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
            self.conn.execute("PRAGMA optimize")

    def checkpoint(self) -> None:
        with self._lock:
            if not self._closed:
                self.conn.execute("PRAGMA wal_checkpoint(PASSIVE)")

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            try:
                self.conn.execute("PRAGMA optimize")
                self.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            except sqlite3.Error:
                # Shutdown must remain best-effort; the connection is still closed.
                pass
            self.conn.close()
            self._closed = True
