import unittest

from modules.titles_analyzer import TitlesAnalyzer


class TestTitlesAnalyzer(unittest.TestCase):
    def test_normalize_heading_text(self):
        text = "  Titre\u200b   AVEC   espaces\t\n"
        normalized = TitlesAnalyzer.normalize_heading_text(text)
        self.assertEqual(normalized, "titre avec espaces")

    def test_compute_hierarchy_inconsistencies(self):
        headings = [
            {"dom_level": 1, "text_raw": "H1", "selector": "/html/body/h1[1]"},
            {"dom_level": 3, "text_raw": "H3", "selector": "/html/body/h3[1]"},
            {"dom_level": 2, "text_raw": "H2", "selector": "/html/body/h2[1]"},
        ]
        incoherences = TitlesAnalyzer.compute_hierarchy_inconsistencies(headings)
        self.assertEqual(len(incoherences), 1)
        self.assertEqual(incoherences[0]["prev_level"], 1)
        self.assertEqual(incoherences[0]["curr_level"], 3)

    def test_compute_ai_mismatches_strict_matching(self):
        dom_headings = [
            {"text_normalized": TitlesAnalyzer.normalize_heading_text("Introduction")},
            {"text_normalized": TitlesAnalyzer.normalize_heading_text("Contactez-nous")},
        ]
        ai_detections = [
            {"text_detected": " introduction ", "ai_confidence": 0.9},
            {"text_detected": "Plan du site", "ai_confidence": 0.8},
        ]
        mismatches = TitlesAnalyzer.compute_ai_mismatches(ai_detections, dom_headings)
        self.assertEqual(len(mismatches), 1)
        self.assertEqual(mismatches[0]["text_detected"], "Plan du site")

    def test_enrich_sections_with_ai_results(self):
        sections = [
            {
                "heading_index": 0,
                "heading_text": "Titre 1",
                "heading_level": 1,
                "start_selector": "/html/body/h1[1]",
                "end_heading_index": 1,
                "end_selector": "/html/body/h2[1]",
            },
            {
                "heading_index": 1,
                "heading_text": "Titre 2",
                "heading_level": 2,
                "start_selector": "/html/body/h2[1]",
                "end_heading_index": 1,
                "end_selector": "/html/body/h2[1]",
            },
        ]
        ai_results = {
            0: {"ok": 1, "score": 0.92, "comment": "Section cohérente"},
        }
        enriched = TitlesAnalyzer.enrich_sections_with_ai_results(sections, ai_results)
        self.assertEqual(enriched[0]["ai_ok"], 1)
        self.assertEqual(enriched[0]["ai_score"], 0.92)
        self.assertEqual(enriched[0]["ai_comment"], "Section cohérente")
        self.assertEqual(enriched[1]["ai_ok"], "")
        self.assertEqual(enriched[1]["ai_comment"], "pending_ai_review")

    def test_compute_note_9_1_2(self):
        all_ok = [{"ai_ok": 1}, {"ai_ok": 1}]
        with_pending = [{"ai_ok": 1}, {"ai_ok": ""}]
        with_ko = [{"ai_ok": 1}, {"ai_ok": 0}]
        self.assertEqual(TitlesAnalyzer.compute_note_9_1_2(all_ok), 1)
        self.assertEqual(TitlesAnalyzer.compute_note_9_1_2(with_pending), 0)
        self.assertEqual(TitlesAnalyzer.compute_note_9_1_2(with_ko), 0)

    def test_extract_json_from_text(self):
        wrapped_object = "Réponse:\n{\"ok\": 1, \"score\": 0.7, \"comment\": \"ok\"}\nMerci"
        wrapped_list = "```json\n[{\"text_detected\":\"Titre\", \"ai_confidence\":0.8}]\n```"
        parsed_obj = TitlesAnalyzer._extract_json_from_text(wrapped_object)
        parsed_list = TitlesAnalyzer._extract_json_from_text(wrapped_list)
        self.assertIsInstance(parsed_obj, dict)
        self.assertEqual(parsed_obj.get("ok"), 1)
        self.assertIsInstance(parsed_list, list)
        self.assertEqual(parsed_list[0].get("text_detected"), "Titre")

    def test_compute_ai_coverage_9_1_2(self):
        sections = [
            {"section_screenshot_path": "a.png", "ai_provider": "api", "ai_ok": 1},
            {"section_screenshot_path": "b.png", "ai_provider": "missing_api_key", "ai_ok": ""},
            {"section_screenshot_path": "", "ai_provider": "", "ai_ok": ""},
        ]
        coverage = TitlesAnalyzer._compute_ai_coverage_9_1_2(sections)
        self.assertEqual(coverage["total_sections"], 3)
        self.assertEqual(coverage["with_screenshot"], 2)
        self.assertEqual(coverage["api_count"], 1)
        self.assertEqual(coverage["fallback_count"], 1)
        self.assertEqual(coverage["pending_count"], 2)


if __name__ == "__main__":
    unittest.main()
