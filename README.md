# Daily M’Cheyne Bible Reading

A small GitHub Pages site that publishes the current day’s Robert Murray M’Cheyne readings in clean, reader-friendly ESV text. It is designed to be imported into ElevenReader from one permanent URL.

## What it does

- Uses the standard 365-day M’Cheyne calendar.
- Displays the two **Family** readings under “Morning.”
- Displays the two **Private/Secret** readings under “Evening.”
- Retrieves official ESV text from Crossway’s API.
- Omits verse numbers and footnotes for smoother listening.
- Updates overnight using GitHub Actions.
- Determines the calendar date in `America/Boise`, including daylight-saving changes.
- Replaces only `index.html`; yesterday’s text is not retained by the site.

February 29 uses the February 28 reading because the plan has 365 entries keyed by month and day.

## One-time setup

### Automatic Windows setup

Open the extracted folder in VS Code, open a PowerShell terminal, and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup-and-deploy.ps1
```

The script checks its target before changing Git remotes, runs the tests, creates or reuses only `cwarloe/daily-bible-reading`, prompts privately for the ESV key, enables Pages, and launches today’s workflow. Git, Python, GitHub CLI, and an authenticated `gh` session are required.

### Manual setup

1. Create a public GitHub repository named `daily-bible-reading` and put these files on its `main` branch.
2. In the repository, open **Settings → Secrets and variables → Actions → New repository secret**.
3. Name the secret `ESV_API_KEY` and paste the ESV API key as its value.
4. Open **Settings → Pages**.
5. Under **Build and deployment → Source**, choose **GitHub Actions**.
6. Open **Actions → Update Daily Bible Reading → Run workflow**. Optionally enter a date such as `2026-09-07` for testing.
7. After Pages finishes publishing, open `https://YOUR-USERNAME.github.io/daily-bible-reading/`.
8. Import that URL with the ElevenReader browser extension and confirm that the Morning/Evening headings and passage headings are handled cleanly.

The scheduled job runs at 09:17 UTC, which is 2:17 a.m. MST or 3:17 a.m. MDT. The precise time is unimportant; the generated date always comes from Boise local time.

## Local test

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
ESV_API_KEY="your-key" python generate_page.py --date 2026-09-07
```

On Windows PowerShell, activate with `.venv\\Scripts\\Activate.ps1` and set the key with `$env:ESV_API_KEY="your-key"`.

## Operational notes

- Never put the ESV key directly in Python, HTML, or workflow YAML.
- The generator finishes all API requests before replacing `index.html`, so a failed request does not publish a partial page.
- A manually supplied test date affects the generated page until the next scheduled run.
- The workflow deploys with GitHub’s official Pages actions. It also commits the changed page daily, providing normal repository activity and a readable history of successful generations.
- The ESV text and reading-plan data should not be released under a Creative Commons license. No repository license is included.

## Sources

- M’Cheyne calendar: <https://www.mcheyne.info/calendar.pdf>
- ESV API: <https://api.esv.org/>
- ESV passage-text options: <https://api.esv.org/docs/passage-text/>
- ElevenReader imports: <https://elevenlabs.io/docs/help-center/product/mobile-apps/eleven-reader/how-do-i-add-content-to-eleven-reader>
