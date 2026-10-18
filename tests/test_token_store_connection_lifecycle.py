from contextlib import closing
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild.token_store import TwitchTokenStore


class TokenStoreConnectionLifecycleTests(unittest.TestCase):
    def test_all_operations_close_connections_including_sql_failure(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'tokens.db'
            original=TwitchTokenStore._connect
            opened=[]
            def tracking(store):
                conn=original(store)
                opened.append(conn)
                return conn
            with patch.object(TwitchTokenStore,'_connect',tracking):
                store=TwitchTokenStore(path)
                store.upsert('111','test-token','test-refresh')
                self.assertEqual(store.count(),1)
                self.assertEqual(store.get('111')['user_id'],'111')
                self.assertEqual(store.user_ids(),{'111'})
                self.assertEqual(len(store.load()),1)
                store.delete('111')
                self.assertEqual(store.count(),0)
                # Forced SQL error inside the read transaction still closes the handle.
                with closing(sqlite3.connect(path)) as setup, setup:
                    setup.execute('DROP TABLE twitch_tokens')
                with self.assertRaises(sqlite3.OperationalError):
                    store.load()
            self.assertGreaterEqual(len(opened),8)
            for conn in opened:
                with self.assertRaises(sqlite3.ProgrammingError):
                    conn.execute('SELECT 1')

if __name__=='__main__':unittest.main()
