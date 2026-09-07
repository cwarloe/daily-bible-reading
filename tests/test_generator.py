import tempfile
import unittest
from datetime import date
from pathlib import Path

import generate_page


class GeneratorTests(unittest.TestCase):
    def test_plan_has_every_non_leap_date(self):
        plan = generate_page.load_plan()
        self.assertEqual(365, len(plan))
        self.assertNotIn("02-29", plan)
        for key, day in plan.items():
            self.assertRegex(key, r"^\d{2}-\d{2}$")
            self.assertEqual({"family", "private"}, set(day))
            self.assertEqual(2, len(day["family"]))
            self.assertEqual(2, len(day["private"]))
            self.assertTrue(all(ref.strip() for refs in day.values() for ref in refs))

    def test_known_dates_match_mcheyne_calendar(self):
        plan = generate_page.load_plan()
        self.assertEqual(["Genesis 1", "Matthew 1"], plan["01-01"]["family"])
        self.assertEqual(["Ezra 1", "Acts 1"], plan["01-01"]["private"])
        self.assertEqual(["2 Samuel 1", "1 Corinthians 12"], plan["09-07"]["family"])
        self.assertEqual(["Ezekiel 10", "Psalms 49"], plan["09-07"]["private"])
        self.assertEqual(["2 Chronicles 36", "Revelation 22"], plan["12-31"]["family"])
        self.assertEqual(["Malachi 4", "John 21"], plan["12-31"]["private"])

    def test_invalid_plan_size_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "short.json"
            path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Expected 365"):
                generate_page.load_plan(path)

    def test_rendered_page_is_structured_and_escaped(self):
        plan = {"family": ["Genesis 1", "Matthew 1"], "private": ["Ezra 1", "Acts 1"]}
        texts = {"family": ["First paragraph.\n\nSecond.", "Safe <text>"], "private": ["Text", "Text"]}
        page = generate_page.render_page(date(2026, 1, 1), plan, texts)
        self.assertIn("<!doctype html>", page)
        self.assertIn("Morning — Family Reading", page)
        self.assertIn("Evening — Private Reading", page)
        self.assertIn("Safe &lt;text&gt;", page)
        self.assertIn("ESV.org", page)

    def test_leap_day_uses_february_28_key(self):
        self.assertEqual("02-28", generate_page.schedule_key(date(2028, 2, 29)))


if __name__ == "__main__":
    unittest.main()
