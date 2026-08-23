from __future__ import annotations

import argparse
import random
import tempfile
import threading
import time
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.player_snapshot import PortalRepository


ROOT = Path(__file__).resolve().parent
STARTERS = ("warrior", "monk", "thief", "blackmage", "whitemage", "redmage")


def _reader_worker(
    db_path: Path,
    data_dir: Path,
    usernames: list[str],
    stop: threading.Event,
    stats: dict[str, int],
    lock: threading.Lock,
    seed: int,
) -> None:
    rng = random.Random(seed)
    repo = PortalRepository(db_path, data_dir)
    local_reads = 0
    local_errors = 0
    try:
        while not stop.is_set():
            try:
                # Model live Portal behavior instead of an impossible hot loop:
                # most refreshes are one profile read, while the full Registry is
                # revisited periodically. A tiny pause mirrors browser/SSE cadence
                # and prevents the synthetic readers from monopolizing the Python
                # process rather than testing SQLite concurrency.
                if local_reads % 40 == 0:
                    repo.list_players()
                else:
                    repo.overview(rng.choice(usernames))
                local_reads += 1
                time.sleep(0.002)
            except Exception:
                local_errors += 1
                time.sleep(0.001)
    finally:
        repo.close()
        with lock:
            stats["reads"] += local_reads
            stats["errors"] += local_errors


def run_stress(players: int, operations: int, readers: int, seed: int) -> dict[str, object]:
    players = max(10, min(2000, int(players)))
    operations = max(players, min(100000, int(operations)))
    readers = max(0, min(16, int(readers)))
    rng = random.Random(seed)

    with tempfile.TemporaryDirectory(prefix="crystal-guild-stress-") as tmp:
        tmp_path = Path(tmp)
        db_path = tmp_path / "stress.db"
        overlay = tmp_path / "overlay.json"
        data_dir = ROOT / "data"
        db = Database(db_path)
        data = GameData(data_dir)
        data.validate_or_raise()
        game = CrystalGuildEngine(
            db,
            data,
            venture_cooldown_seconds=0,
            overlay_state_path=str(overlay),
            rng=rng,
        )

        usernames: list[str] = []
        started = time.perf_counter()
        for index in range(players):
            pid = str(index + 1)
            username = f"stress{index + 1}"
            usernames.append(username)
            result = game.recruit(pid, username, f"Stress {index + 1}")
            if not result.ok:
                raise RuntimeError(result.messages[0])
            chosen = game.choose_job(pid, STARTERS[index % len(STARTERS)])
            if not chosen.ok:
                raise RuntimeError(chosen.messages[0])

        stop = threading.Event()
        reader_stats = {"reads": 0, "errors": 0}
        reader_lock = threading.Lock()
        threads = [
            threading.Thread(
                target=_reader_worker,
                args=(db_path, data_dir, usernames, stop, reader_stats, reader_lock, seed + 1000 + i),
                daemon=True,
            )
            for i in range(readers)
        ]
        for thread in threads:
            thread.start()

        monsters = sorted(data.monsters.values(), key=lambda item: int(item["level"]))
        for op_index in range(operations):
            pid = str(rng.randint(1, players))
            action = op_index % 7
            if action in {0, 1, 2, 3}:
                player = db.one("SELECT * FROM players WHERE twitch_id=?", (pid,))
                # Keep the stress run representative instead of feeding Level 1
                # heroes superboss-scale enemies simply to create large numbers.
                eligible = [m for m in monsters if int(m["level"]) <= max(5, int(player["level"]) + 4)]
                game._award_victory(pid, player, rng.choice(eligible or monsters[:5]))
            elif action == 4:
                game._change_item(pid, "potion", 1, "ultima_stress")
            elif action == 5:
                if game._inventory_qty(pid, "potion") > 1:
                    game.sell(pid, "potion", 1)
                else:
                    game._change_item(pid, "potion", 1, "ultima_stress")
            else:
                game.hero(pid)

        stop.set()
        for thread in threads:
            thread.join(timeout=5)

        elapsed = max(0.000001, time.perf_counter() - started)
        integrity = db.integrity_report()
        negative_gil = int(db.one("SELECT COUNT(*) AS n FROM players WHERE gil < 0")["n"])
        negative_inventory = int(db.one("SELECT COUNT(*) AS n FROM inventory WHERE quantity < 0")["n"])
        player_count = int(db.one("SELECT COUNT(*) AS n FROM players")["n"])
        job_count = int(db.one("SELECT COUNT(*) AS n FROM player_jobs")["n"])
        runtime = game.runtime_status()
        tx = db.transaction_stats()
        db.close()

        ok = bool(
            integrity["ok"]
            and player_count == players
            and job_count >= players
            and negative_gil == 0
            and negative_inventory == 0
            and reader_stats["errors"] == 0
            and int(tx["depth"]) == 0
            and runtime["active"] == "idle"
        )
        return {
            "ok": ok,
            "players": player_count,
            "operations": operations,
            "portal_reads": reader_stats["reads"],
            "portal_read_errors": reader_stats["errors"],
            "elapsed_seconds": elapsed,
            "operations_per_second": operations / elapsed,
            "transactions": integrity["transactions"],
            "negative_gil_rows": negative_gil,
            "negative_inventory_rows": negative_inventory,
            "journal_mode": integrity["journal_mode"],
            "foreign_key_violations": len(integrity["foreign_key_violations"]),
            "quick_check_failures": len(integrity["quick_check"]),
            "tx_rollbacks": tx["rollbacks"],
            "savepoint_rollbacks": tx["savepoint_rollbacks"],
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Crystal Guild v1.1.15 Wayfarer synthetic release stress test")
    parser.add_argument("--players", type=int, default=500, help="Synthetic heroes (10-2000; default 500)")
    parser.add_argument("--operations", type=int, default=5000, help="Gameplay/read operations (default 5000)")
    parser.add_argument("--readers", type=int, default=4, help="Concurrent portal readers (0-16; default 4)")
    parser.add_argument("--seed", type=int, default=99, help="Deterministic random seed")
    args = parser.parse_args()

    print("Crystal Guild v1.1.15 — Wayfarer Synthetic Stress Test")
    result = run_stress(args.players, args.operations, args.readers, args.seed)
    print(
        f"players={result['players']:,} operations={result['operations']:,} "
        f"portal_reads={result['portal_reads']:,} elapsed={result['elapsed_seconds']:.2f}s "
        f"throughput={result['operations_per_second']:.1f} ops/s"
    )
    print(
        f"ledger={result['transactions']:,} journal={result['journal_mode']} "
        f"quick_failures={result['quick_check_failures']} fk_violations={result['foreign_key_violations']} "
        f"negative_gil={result['negative_gil_rows']} negative_inventory={result['negative_inventory_rows']} "
        f"portal_errors={result['portal_read_errors']} rollbacks={result['tx_rollbacks']}"
    )
    print("CLOUD RUNTIME STRESS PASS" if result["ok"] else "CLOUD RUNTIME STRESS FAIL")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
