import unittest

from src.quality import assess


class QualityTests(unittest.TestCase):
    def test_strong_evidence_can_reach_top_tier(self):
        quality = assess(
            score=90,
            evidence=["A sufficiently long operational evidence sentence that can be reviewed."] * 4,
            opportunities=["workflow automation", "follow-up automation", "reporting"],
            url="https://example.com",
        )
        self.assertEqual(quality.tier, "A")
        self.assertGreaterEqual(quality.priority, 75)

    def test_thin_evidence_stays_conservative(self):
        quality = assess(score=70, evidence=["tiny"], opportunities=[], url="example")
        self.assertLess(quality.confidence, 65)
        self.assertNotEqual(quality.tier, "A")


if __name__ == "__main__":
    unittest.main()
