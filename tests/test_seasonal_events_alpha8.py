import tempfile
import unittest
from pathlib import Path

from crystal_guild.database import DATABASE_SCHEMA_VERSION, Database
from crystal_guild.seasonal_events import (
    EDITION_ID, SEASONAL_VARIANTS, event_state, set_event_control,
    award_seasonal_kill, award_adventure, award_warden_clear, buy_reward, public_snapshot,
)

class SeasonalEventsAlpha8Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.db=Database(Path(self.tmp.name)/"guild.db"); self.conn=self.db.conn
        self.pid="100"; self.conn.execute("INSERT INTO players(twitch_id,username,display_name) VALUES (?,?,?)",(self.pid,"van","Van")); self.conn.commit()
    def tearDown(self): self.db.close(); self.tmp.cleanup()
    def test_schema_and_disabled_default(self):
        self.assertEqual(DATABASE_SCHEMA_VERSION,22); self.assertEqual(self.db.schema_version(),22)
        state=event_state(self.conn); self.assertEqual(state["edition_id"],EDITION_ID); self.assertEqual(state["state"],"disabled"); self.assertFalse(state["active"])
    def test_manual_control_and_seasonal_collection(self):
        set_event_control(self.conn,enabled=True,paused=False,activation_mode="manual")
        self.assertTrue(event_state(self.conn)["active"])
        total=0
        for variant in SEASONAL_VARIANTS:
            result=award_seasonal_kill(self.conn,self.pid,variant["id"],today_key="2026-10-31"); total+=int(result["tokens"])
        snap=public_snapshot(self.conn,self.pid)
        self.assertEqual(len([x for x in snap["variants"] if x["clears"]>0]),4)
        trophy_ids={x["id"] for x in snap["trophies"] if x["unlocked_at"]}
        self.assertIn("season_halloween_first",trophy_ids); self.assertIn("season_halloween_four",trophy_ids); self.assertGreaterEqual(total,12)
    def test_daily_objectives_and_warden_first_clear_are_idempotent(self):
        set_event_control(self.conn,enabled=True,activation_mode="manual")
        for _ in range(3): award_seasonal_kill(self.conn,self.pid,"jack_o_bomb",today_key="2026-10-31")
        award_adventure(self.conn,self.pid,today_key="2026-10-31"); award_adventure(self.conn,self.pid,today_key="2026-10-31")
        first=award_warden_clear(self.conn,self.pid); second=award_warden_clear(self.conn,self.pid)
        self.assertEqual(first["tokens"],15); self.assertEqual(second["tokens"],0)
        claims=self.conn.execute("SELECT COUNT(*) FROM player_seasonal_objective_claims WHERE player_id=?",(self.pid,)).fetchone()[0]
        self.assertGreaterEqual(claims,2)
    def test_moonlit_shop_ownership_and_keeper_trophy(self):
        set_event_control(self.conn,enabled=True,activation_mode="manual")
        self.conn.execute("INSERT INTO player_seasonal_event_progress(player_id,edition_id,tokens) VALUES (?,?,100)",(self.pid,EDITION_ID))
        ok,msg,_=buy_reward(self.conn,self.pid,"hollow_crystal_display"); self.assertTrue(ok); self.assertIn("Hollow Crystal Display",msg)
        ok2,_,_=buy_reward(self.conn,self.pid,"hollow_crystal_display"); self.assertFalse(ok2)
        snap=public_snapshot(self.conn,self.pid); self.assertTrue(next(x for x in snap["trophies"] if x["id"]=="season_halloween_keeper")["unlocked_at"])

if __name__=='__main__': unittest.main()
