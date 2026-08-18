import unittest

from src.entity import company_key, normalize_company_name
from src.lead_agent import analyze_text, root_name
from src.lead_matching import match_offers, rank_lead
from src.outreach import draft_outreach


class LeadAgentTests(unittest.TestCase):
    def test_detects_non_obvious_operational_signals(self):
        text = (
            "We provide 24/7 emergency HVAC service. Our technicians cover a broad service area. "
            "We offer same day estimates and maintenance plans."
        )
        score, signals, opportunities, evidence = analyze_text(text)
        self.assertGreater(score, 0)
        self.assertTrue(any("24/7" in x.lower() for x in signals))
        self.assertTrue(opportunities)
        self.assertTrue(evidence)

    def test_matching_turns_signals_into_offers(self):
        offers = match_offers(["missed-call capture and instant follow-up automation"], ["missed call: lost revenue"])
        self.assertTrue(offers)
        self.assertEqual(offers[0]["offer"], "Missed-call recovery")

    def test_rank_is_conservative(self):
        self.assertEqual(rank_lead(80, 1, 1)[0], "C")
        self.assertEqual(rank_lead(80, 8, 8)[0], "A")
        self.assertEqual(rank_lead(50, 5, 5)[0], "B")

    def test_outreach_uses_evidence_and_does_not_send(self):
        draft = draft_outreach({"name": "Example Co", "evidence": ["They offer 24/7 service."], "opportunities": ["after-hours intake automation"]})
        self.assertIn("24/7 service", draft["body"])
        self.assertIn("after-hours intake automation", draft["body"])
        self.assertIn("Example Co", draft["subject"])

    def test_entity_normalization(self):
        self.assertEqual(normalize_company_name("Example Company, LLC"), "example")
        self.assertEqual(company_key("Example", "https://www.example.com/about"), "example.com")

    def test_root_name(self):
        self.assertEqual(root_name("https://www.example.com/about"), "example.com")


if __name__ == "__main__":
    unittest.main()
