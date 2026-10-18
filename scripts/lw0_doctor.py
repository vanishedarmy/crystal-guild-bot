"""Read-only LW-0 foundation diagnostic. Run from any folder.

    python Bot/scripts/lw0_doctor.py --db /path/to/guild.db
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from crystal_guild.data import GameData  # noqa: E402
from crystal_guild.database import DATABASE_SCHEMA_VERSION  # noqa: E402


def inspect(db_path: Path | None) -> dict:
    data = GameData(ROOT / 'data')
    errors = data.validate()
    result = {
        'milestone': 'LW-0',
        'schema_expected': DATABASE_SCHEMA_VERSION,
        'regions': [r['id'] for r in data.living_world_regions],
        'feature_enabled': data.living_world_config['enabled'],
        'playable': data.living_world_config['playable'],
        'offline_completion_required': data.living_world_config['offline_completion_required'],
        'catalog_errors': errors,
        'database': None,
        'ok': not errors,
    }
    if db_path is not None:
        db_path = db_path.expanduser().resolve()
        if not db_path.is_file():
            result['database'] = {'error': 'database file not found'}
            result['ok'] = False
        else:
            with sqlite3.connect(f'file:{db_path.as_posix()}?mode=ro', uri=True) as conn:
                version = int(conn.execute('SELECT COALESCE(MAX(version),1) FROM schema_migrations').fetchone()[0])
                quick = str(conn.execute('PRAGMA quick_check').fetchone()[0])
                foreign_violations = len(conn.execute('PRAGMA foreign_key_check').fetchall())
                tables = {x[0] for x in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'lw_%'")}
                result['database'] = {
                    'schema_version': version,
                    'quick_check': quick,
                    'foreign_key_violations': foreign_violations,
                    'living_world_tables': len(tables),
                    'players': int(conn.execute('SELECT COUNT(*) FROM players').fetchone()[0]),
                }
                result['ok'] &= version >= DATABASE_SCHEMA_VERSION and quick == 'ok' and not foreign_violations and len(tables) == 7
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, help='Optional local Guild SQLite database (read only)')
    args = parser.parse_args()
    report = inspect(args.db)
    print(json.dumps(report, indent=2))
    sys.exit(0 if report['ok'] else 1)
