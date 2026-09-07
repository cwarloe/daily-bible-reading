# Codex handoff

The repository implementation is complete in this package. Do not redesign or expand it.

## Goal

Publish a permanent GitHub Pages URL containing the current Boise-local day’s M’Cheyne ESV readings, structured for import into ElevenReader.

## Required actions

1. Create or use the user’s `daily-bible-reading` repository.
2. Copy this package to the repository root without changing the schedule or architecture.
3. Run `python -m unittest discover -s tests -v`.
4. Commit and push to `main`.
5. Ask the user to add their existing ESV key as the Actions secret `ESV_API_KEY`; never request that they paste the key into chat or source code.
6. Configure GitHub Pages with **Source: GitHub Actions**.
7. Manually run **Update Daily Bible Reading** with date `2026-09-07`.
8. Confirm that the published page shows:
   - Morning: 2 Samuel 1; 1 Corinthians 12
   - Evening: Ezekiel 10; Psalms 49
9. Return the GitHub Pages URL and any action the user still must take.

Do not create audio, call ElevenLabs APIs, add tracking, or expose the ESV key.
