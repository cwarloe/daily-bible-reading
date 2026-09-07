# Daily M'Cheyne Bible Reading

Permanent page: https://cwarloe.github.io/daily-bible-reading/

One clean page with Morning / Family and Evening / Private readings, fetched
from the official ESV API without verse numbers or footnotes. No audio,
tracking, archives, or Reader API integration. Import the URL manually.

The GitHub Actions workflow runs at 09:17 UTC (02:17 MST / 03:17 MDT),
with backup runs at 11:17 and 12:17 UTC (05:17 and 06:17 MDT;
04:17 and 05:17 MST). Each attempt regenerates and verifies the current page.
GitHub can delay or drop scheduled events; these backups reduce the impact of
a missed trigger but do not guarantee delivery by a particular time.
The date is always today's date in America/Boise. Manual workflow runs also
use today; there is no production date override. February 29 repeats February
28 without shifting March. See validation/README.md for the full calendar audit.

## Deployment

GitHub Pages uses the GitHub Actions source. `ESV_API_KEY` belongs only in the
repository Actions secrets. Generated HTML goes to ignored `_site/index.html`,
is uploaded to Pages, and is checked against the live URL after deployment.
The temporary Actions artifact is deleted after the run (one-day expiration
as a fallback). No ESV text is committed or cached by the workflow. Pages serves
only the latest deployment, although GitHub controls its infrastructure retention.
A monthly empty commit prevents GitHub's 60-day inactivity schedule disablement;
it contains no generated files. Failed API requests leave the current site intact.

## Validation

Install requirements.txt, then run `python -m unittest discover -s tests -v`.
`tzdata` supports Windows. Local `--date` is for testing only and is never used
by the publishing workflow. `verify_live.py` verifies date, four headings,
attribution, and byte-for-byte equality with the freshly generated page.
The legacy setup-and-deploy.ps1 is superseded by direct GitHub Actions deployment.

## ESV usage terms reviewed

https://api.esv.org/ permits noncommercial website integration but sets distinct
query, storage, display, and redistribution limits. The 500-verse ceiling alone
is not sufficient: storage and page display are also limited to half a book.
The short-book exception is stated for queries, not for storage or page display.
For example, this annual plan includes all of Philemon, 2 John, 3 John, Jude,
and Obadiah on their assigned days; Haggai 2 also exceeds half that book by verses.
Redistribution has an additional limit on Scripture's proportion of the work.
A Scripture-only Reader import cannot simply be assumed to satisfy that condition.
Personal use and a private source repository do not establish an exception to
these stated terms. This implementation follows the requested personal reading
schedule; it does not assert that the full use is covered by the standard terms.
Any necessary additional rights remain the account holder's responsibility.

The page includes Crossway's required attribution and an ESV.org link. The key
is never exposed in page content or logs. Keeping yesterday's imported content
in Reader is outside this application's storage controls.
