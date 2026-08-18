import unittest

from src.lead_agent import analyze_text, root_name


class LeadAgentTests(unittest.TestCase):
    def test_detects_non_obvious_operational_signals(self):
        text = (
            "We provide 24/7 emergency HVAC service. Our technicians cover a broad service area. "
            "We offer same day estimates and maintenance plans."
        )
        score, signals, opportunities, evidence = analyze_text(text)
        self.assertGreater(score, 0)
        self.assertTrue(any("dispatch" in x.lower() or "24/7" in x.lower() for x in signals))
        self.assertTrue(opportunities)
        self.assertTrue(evidence)

    def test_root_name(self):
        self.assertEqual(root_name("https://www.example.com/about"), "example.com")


if __name__ == "__main__":
    unittest.main()
