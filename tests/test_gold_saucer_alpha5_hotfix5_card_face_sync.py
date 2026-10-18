import unittest

from crystal_guild.gold_saucer import TRIPLE_TRIAD_CARDS_BY_ID


class TripleTriadCardFaceSyncTests(unittest.TestCase):
    def test_all_printed_card_face_values_are_authoritative(self):
        expected = {
            "chocobo": (3, 4, 2, 1),
            "moogle": (2, 3, 4, 3),
            "cactuar": (5, 2, 1, 5),
            "bomb": (4, 2, 6, 2),
            "flan": (1, 5, 4, 3),
            "tonberry": (6, 2, 5, 3),
            "coeurl": (4, 6, 3, 5),
            "ahriman": (5, 4, 6, 3),
            "malboro": (6, 5, 5, 4),
            "ifrit": (7, 5, 6, 6),
            "shiva": (6, 7, 5, 6),
            "ramuh": (7, 6, 7, 4),
            "leviathan": (8, 7, 5, 6),
            "bahamut": (8, 8, 7, 7),
            "odin": (9, 7, 8, 6),
        }
        self.assertEqual(len(TRIPLE_TRIAD_CARDS_BY_ID), 45)
        self.assertLessEqual(set(expected), set(TRIPLE_TRIAD_CARDS_BY_ID))
        for card_id, values in expected.items():
            card = TRIPLE_TRIAD_CARDS_BY_ID[card_id]
            actual = (card["top"], card["right"], card["bottom"], card["left"])
            self.assertEqual(actual, values, card_id)


if __name__ == "__main__":
    unittest.main()
