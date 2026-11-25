import unittest
from datetime import datetime, timezone

from report import build_result_html, result_filename


class BuildResultHtmlTests(unittest.TestCase):
    def test_builds_self_contained_report_with_candidate_data(self):
        candidate = {
            "file_name": "Анна Иванова.txt",
            "verdict": "подходит",
            "result": {
                "score": 84,
                "summary": "Подходит <по основным требованиям>.",
                "strengths": ["Python"],
                "gaps": [],
                "evidence": [{
                    "requirement": "Python",
                    "status": "подтверждено",
                    "quote": "Python — 5 лет",
                    "reasoning": "Есть прямое подтверждение.",
                }],
                "missing_information": [],
                "interview_questions": ["Расскажите о проекте."],
            },
        }

        output = build_result_html(candidate, generated_at=datetime(2026, 1, 2, tzinfo=timezone.utc))

        self.assertIn("<!doctype html>", output)
        self.assertIn('name="viewport"', output)
        self.assertIn("вввв.txt", output)
        self.assertIn("84/100", output)
        self.assertIn("&lt;по основным требованиям&gt;", output)
        self.assertNotIn("<img", output.lower())
        self.assertNotIn("https://", output)
        self.assertTrue(result_filename(candidate).endswith(".html"))


if __name__ == "__main__":
    unittest.main()
