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

class AnnualAuditTests(unittest.TestCase):
    def test_every_reading_matches_pdf_with_documented_errata(self):
        import json
        source = json.loads((generate_page.ROOT / 'validation/calendar-extracted.json').read_text())
        source['03-06']['private'][1] = '2 Corinthians 5'
        source['05-11']['private'][0] = 'Isaiah 9:8-21; Isaiah 10:1-4'
        self.assertEqual(source, generate_page.load_plan())

    def test_all_leap_year_dates_keep_calendar_alignment(self):
        from datetime import timedelta
        plan = generate_page.load_plan()
        for offset in range(366):
            current = date(2028, 1, 1) + timedelta(days=offset)
            expected = '02-28' if current == date(2028, 2, 29) else current.strftime('%m-%d')
            self.assertEqual(plan[expected], plan[generate_page.schedule_key(current)])

    def test_boise_date_at_utc_midnight_and_dst(self):
        from datetime import datetime, timezone
        from unittest.mock import patch
        for utc, expected in [('2026-09-07T01:00:00', date(2026,9,6)),
                              ('2026-01-02T06:59:00', date(2026,1,1)),
                              ('2026-01-02T07:00:00', date(2026,1,2)),
                              ('2026-03-08T09:01:00', date(2026,3,8))]:
            instant = datetime.fromisoformat(utc).replace(tzinfo=timezone.utc)
            with patch('generate_page.datetime') as clock:
                clock.now.return_value = instant.astimezone(generate_page.BOISE)
                self.assertEqual(expected, generate_page.target_date())
                clock.now.assert_called_once_with(generate_page.BOISE)

    def test_api_options_and_multiple_passages(self):
        from unittest.mock import Mock
        session = Mock()
        session.get.return_value.json.return_value = {'passages': ['First.', 'Second. (ESV)']}
        self.assertEqual('First.\n\nSecond. (ESV)',
                         generate_page.fetch_passage(session, 'test-only', 'Jeremiah 36; Jeremiah 45'))
        options = session.get.call_args.kwargs['params']
        for key in ['include-verse-numbers', 'include-first-verse-numbers', 'include-footnotes', 'include-footnote-body']:
            self.assertEqual('false', options[key])
        session.get.return_value.json.return_value = {'passages': []}
        with self.assertRaises(RuntimeError):
            generate_page.fetch_passage(session, 'test-only', 'Genesis 1')
        session.get.return_value.raise_for_status.side_effect = generate_page.requests.HTTPError('unauthorized')
        with self.assertRaises(generate_page.requests.HTTPError):
            generate_page.fetch_passage(session, 'test-only', 'Genesis 1')

    def test_failed_fetch_does_not_replace_page(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'index.html'
            output.write_text('Existing page')
            with patch.object(generate_page, 'OUTPUT_PATH', output), patch('sys.argv', ['generate_page.py']), \
                 patch.dict(generate_page.os.environ, {'ESV_API_KEY': 'test-only'}), \
                 patch.object(generate_page, 'fetch_passage', side_effect=RuntimeError('API failure')):
                with self.assertRaises(RuntimeError):
                    generate_page.main()
            self.assertEqual('Existing page', output.read_text())

    def test_live_verification_rejects_stale_date_and_wrong_readings(self):
        from verify_live import verify
        day = date(2026, 9, 6)
        plan = generate_page.load_plan()['09-06']
        texts = {'family': ['Test.', 'Test.'], 'private': ['Test.', 'Test.']}
        page = generate_page.render_page(day, plan, texts)
        verify(page, day)
        with self.assertRaises(ValueError):
            verify(page, date(2026, 9, 7))
        with self.assertRaises(ValueError):
            verify(page.replace('Ezekiel 9', 'John 11'), day)


if __name__ == "__main__":
    unittest.main()
