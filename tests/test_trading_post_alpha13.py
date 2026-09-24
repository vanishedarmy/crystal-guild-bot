"""Alpha 13 Trading Post watchlist, completed-sale history and safe relisting."""
import random
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database, DATABASE_SCHEMA_VERSION
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.portal_actions import PortalActionWorker, ACTION_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[1]

class TradingPostAlpha13Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)/"guild.db"
        self.db = Database(self.path)
        self.game = CrystalGuildEngine(self.db,GameData(ROOT/"data"),overlay_state_path=str(Path(self.tmp.name)/"overlay.json"),rng=random.Random(1313))
        for id,name in (("100","seller"),("200","buyer")):
            self.assertTrue(self.game.recruit(id,name,name.title()).ok)
        self.db.execute("UPDATE players SET gil=500000 WHERE twitch_id IN ('100','200')")
        self.db.execute("UPDATE fellowship_facilities SET tier=1 WHERE facility_id='trading_post'")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def give(self,item,quantity):
        self.db.execute("INSERT INTO inventory(player_id,item_id,quantity) VALUES ('100',?,?) "
                        "ON CONFLICT(player_id,item_id) DO UPDATE SET quantity=inventory.quantity+excluded.quantity",(item,quantity))

    def test_schema_and_watchlist_persists_and_replays(self):
        self.assertEqual(DATABASE_SCHEMA_VERSION,25)
        self.assertEqual(self.db.schema_version(),25)
        self.assertEqual(ACTION_PROTOCOL_VERSION,39)
        self.assertIsNotNone(self.db.one("SELECT name FROM sqlite_master WHERE name='trading_post_watchlist'"))
        self.give("iron_ore",5)
        first=self.game.portal_trading_post_watch("100","iron_ore",True,"watch:one")
        self.assertTrue(first.ok,first.messages)
        self.assertEqual(self.game.portal_trading_post_state("100").data["watchlist"],["iron_ore"])
        replay=self.game.portal_trading_post_watch("100","iron_ore",False,"watch:one")
        self.assertTrue(replay.ok)
        self.assertEqual(self.game.portal_trading_post_state("100").data["watchlist"],["iron_ore"])
        self.assertTrue(self.game.portal_trading_post_watch("100","iron_ore",False,"watch:two").ok)
        self.assertFalse(self.game.portal_trading_post_state("100").data["watchlist"])
        self.assertTrue(self.game.portal_trading_post_watch("100","iron_ore",True,"watch:three").ok)
        self.db.close()
        self.db=Database(self.path)
        self.assertEqual(self.db.schema_version(),25)
        self.assertEqual([r["item_id"] for r in self.db.all("SELECT item_id FROM trading_post_watchlist WHERE player_id='100'")],["iron_ore"])

    def test_limit_and_untradeable_rejection(self):
        items=[k for k,i in self.game.data.items.items() if self.game._trading_post_item_allowed(i)]
        self.assertGreater(len(items),30)
        for n,item in enumerate(items[:30]):
            self.assertTrue(self.game.portal_trading_post_watch("100",item,True,f"watch:limit:{n}").ok)
        too_many=self.game.portal_trading_post_watch("100",items[30],True,"watch:limit:31")
        self.assertFalse(too_many.ok)
        self.assertIn("30",too_many.messages[0])
        self.assertTrue(self.game.portal_trading_post_watch("100",items[0],True,"watch:repeat").ok)
        self.assertFalse(self.game.portal_trading_post_watch("100","chef_knife",True,"watch:bad").ok)
        self.assertFalse(self.game.portal_trading_post_watch("100","iron_ore",1,"watch:wrong").ok)
        self.assertEqual(len(self.game.portal_trading_post_state("100").data["watchlist"]),30)

    def test_owned_quantities_including_protected_and_sold_price_stats(self):
        self.give("iron_ore",9)
        self.give("mythril_ore",2)
        for i,(qty,price) in enumerate(((1,100),(3,200),(2,500))):
            listed=self.game.portal_trading_post_list("100","iron_ore",qty,price,f"list:{i}")
            self.assertTrue(listed.ok,listed.messages)
            bought=self.game.portal_trading_post_buy("200",listed.data["listing_id"],f"buy:{i}")
            self.assertTrue(bought.ok,bought.messages)
        current=self.game.portal_trading_post_list("100","mythril_ore",1,900,"list:unsold")
        self.assertTrue(current.ok)
        state=self.game.portal_trading_post_state("100").data
        self.assertEqual(state["owned_quantities"]["iron_ore"],3)
        self.assertEqual(state["owned_quantities"]["mythril_ore"],1)
        self.assertIn("potion",{item["id"] for item in state["catalog_items"]})
        self.assertNotIn("chef_knife",{item["id"] for item in state["catalog_items"]})
        stat=state["price_stats"]["iron_ore"]
        self.assertEqual((stat["sale_count"],stat["units_sold"]),(3,6))
        self.assertAlmostEqual(stat["average_price"],(1*100+3*200+2*500)/6,places=2)
        self.assertEqual((stat["low_price"],stat["high_price"]),(100,500))
        self.assertNotIn("mythril_ore",state["price_stats"])
        recent=state["recent_sales"]
        self.assertEqual(len(recent),3)
        self.assertTrue(all(s["item_id"]=="iron_ore" for s in recent))
        self.assertTrue(all("seller_id" not in sale and "buyer_id" not in sale for sale in recent))
        history=self.game.portal_trading_post_history("100","iron_ore")
        self.assertTrue(history.ok)
        self.assertEqual(len(history.data["sales"]),3)
        self.assertFalse(self.game.portal_trading_post_history("100","chef_knife").ok)
        # Old sales remain in durable ledger but no longer bias recent prices.
        self.db.execute("UPDATE trading_post_listings SET sold_at=? WHERE id=(SELECT MIN(id) FROM trading_post_listings WHERE status='sold')",(int(time.time())-32*86400,))
        fresh=self.game.portal_trading_post_state("100").data
        self.assertEqual(fresh["price_stats"]["iron_ore"]["sale_count"],2)
        self.assertEqual(len(self.game.portal_trading_post_history("100","iron_ore").data["sales"]),2)

    def test_watchlist_lowest_asking_price_survives_newest_200_listing_limit(self):
        self.assertTrue(self.game.portal_trading_post_watch("100","mythril_ore",True,"watch:full-ledger").ok)
        now=int(time.time())
        with self.db.tx() as conn:
            conn.execute("INSERT INTO trading_post_listings(seller_id,item_id,quantity,unit_price,listing_fee,status,created_at,expires_at) "
                         "VALUES ('100','mythril_ore',1,77,1,'active',?,?)",(now-3000,now+3600))
            conn.executemany("INSERT INTO trading_post_listings(seller_id,item_id,quantity,unit_price,listing_fee,status,created_at,expires_at) "
                             "VALUES ('100','iron_ore',1,999,1,'active',?,?)",
                             [(now+i,now+3600) for i in range(205)])
        state=self.game.portal_trading_post_state("100").data
        self.assertEqual(state["watchlist_market"]["mythril_ore"],{"listing_count":1,"min_asking_price":77})
        self.assertTrue(any(row["item"]["id"]=="mythril_ore" and row["unit_price"]==77 for row in state["listings"]))
        self.assertEqual(len({row["id"] for row in state["listings"]}),len(state["listings"]))

    def test_quick_relist_reuses_atomic_listing_rules_and_requires_real_inventory(self):
        self.give("iron_ore",2)
        listing=self.game.portal_trading_post_list("100","iron_ore",2,300,"original")
        self.assertTrue(listing.ok)
        self.assertTrue(self.game.portal_trading_post_buy("200",listing.data["listing_id"],"buy-original").ok)
        no_items=self.game.portal_trading_post_list("100","iron_ore",2,300,"relist-no-items")
        self.assertFalse(no_items.ok)
        self.give("iron_ore",2)
        new=self.game.portal_trading_post_list("100","iron_ore",2,300,"relist-again")
        self.assertTrue(new.ok,new.messages)
        self.assertNotEqual(new.data["listing_id"],listing.data["listing_id"])
        self.assertEqual(new.data["listing_fee"],12)
        same=self.game.portal_trading_post_list("100","iron_ore",2,300,"relist-again")
        self.assertTrue(same.ok)
        self.assertEqual(same.data["listing_id"],new.data["listing_id"])
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM trading_post_listings WHERE seller_id='100' AND status='active'")["n"],1)

    def test_upgrade_from_previous_schema_creates_verified_backup_preserves_sales(self):
        self.give("iron_ore",2)
        sale=self.game.portal_trading_post_list("100","iron_ore",1,88,"migration-original")
        self.assertTrue(sale.ok)
        self.assertTrue(self.game.portal_trading_post_buy("200",sale.data["listing_id"],"migration-buy").ok)
        self.db.close()
        con=sqlite3.connect(self.path)
        con.execute("DROP TABLE trading_post_watchlist")
        con.execute("DROP INDEX idx_trading_post_recent_sold")
        con.execute("DROP INDEX idx_trading_post_sold_by_item")
        con.execute("DELETE FROM schema_migrations WHERE version=25")
        con.commit();con.close()
        self.db=Database(self.path)
        self.assertEqual(self.db.schema_version(),25)
        self.assertTrue(self.db.pre_migration_backup_path and self.db.pre_migration_backup_path.exists())
        self.assertEqual(self.db.one("SELECT status,unit_price FROM trading_post_listings WHERE id=?",(sale.data["listing_id"],))["status"],"sold")
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM players")["n"],2)

    def test_bot_dispatch_keeps_history_passive(self):
        worker=PortalActionWorker(self.game,"https://example.invalid","key")
        first=worker._execute({"id":"watch-through-worker","type":"TRADING_POST_WATCH","payload":{"item_id":"iron_ore","watched":True},"twitch_id":"100","username":"seller","protocol_version":39})
        self.assertTrue(first[0],first[1])
        history=worker._execute({"id":"history-through-worker","type":"TRADING_POST_HISTORY","payload":{"item_id":"iron_ore"},"twitch_id":"100","username":"seller","protocol_version":39})
        self.assertTrue(history[0],history[1])
        self.assertEqual(history[2]["sales"],[])

if __name__=="__main__": unittest.main()
