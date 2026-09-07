# Annual calendar validation

Source: https://www.mcheyne.info/calendar.pdf (retrieved 2026-09-06).
SHA-256: `76bc6e96ad1f59ea6e12ff966f1485ec5ad82022cdf72ae3096f8a366ad46d21`.

`calendar-extracted.json` records all 1,460 readings in the twelve monthly tables
(PDF pages 4-15). The parser checks the number and order of dates in every month.
It normalizes comma-separated consecutive chapters to ranges, repeats the book
for mixed selections and nonconsecutive chapters, expands "Song", and corrects
the spelling "Phillipians". No Scripture text is contained in this fixture.

The production schedule matches this full source fixture with two documented
errata retained from the standard calendar:

- March 6: PDF prints 2 Corinthians 1 between chapters 4 and 6; use chapter 5.
- May 11: PDF prints Isaiah 9:7-21 after May 10 already ends at 9:7; use
  Isaiah 9:8-21 and 10:1-4, avoiding a repeated verse.

These readings are corroborated at https://www.mcheyneplan.com/calendar.html
and https://bibleplan.org/plans/mcheyne/print.
September 7 private readings are Ezekiel 10 and Psalms 49.
All split passages (including Luke 1, Psalm 78 and 119, Exodus 12, Isaiah 9-10,
Deuteronomy 28, Joshua 6, Judges 11, 2 Chronicles 6 and Zechariah 13) are retained.
Jeremiah 36 and 45 are nonconsecutive chapters, not a range.

The PDF has no February 29. This application repeats February 28 on leap day;
March 1 and all subsequent dates keep their usual calendar readings.

To reproduce: download the source to `validation/calendar.pdf`, install `pypdf`,
and run `python validation/audit_calendar.py`. Ordinary tests compare every
production reading with the checked-in extraction and the two errata, and check
all 366 dates in a leap year. The source PDF is not deployed or committed.
