import unittest
from unittest.mock import patch

from src.entity import company_key, normalize_company_name
from src.lead_agent import _decode_result_url, analyze_text, root_name, search_web
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

    def test_search_url_decoding(self):
        self.assertEqual(_decode_result_url("https://duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fpage"), "https://example.com/page")
        self.assertEqual(_decode_result_url("https://example.com/page"), "https://example.com/page")

    @patch("src.lead_agent._search_bing")
    @patch("src.lead_agent._search_duckduckgo")
    def test_multi_engine_search_deduplicates_urls(self, ddg, bing):
        ddg.return_value = [{"title": "A", "url": "https://example.com", "source": "DuckDuckGo"}]
        bing.return_value = [
            {"title": "A", "url": "https://example.com", "source": "Bing"},
            {"title": "B", "url": "https://other.example", "source": "Bing"},
        ]
        results = search_web("example", limit=3)
        self.assertEqual([x["url"] for x in results], ["https://example.com", "https://other.example"])
        self.assertEqual({x["source"] for x in results}, {"DuckDuckGo", "Bing"})


if __name__ == "__main__":
    unittest.main()
