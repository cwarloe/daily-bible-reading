# Daily M'Cheyne Reader: Cloudflare hosting handoff

2026-11-26. **Prepared; not deployed.** Preserve the GitHub Pages daily reading and its nightly/backup workflow until a Cloudflare-hosted replacement has been tested through multiple date changes.

## Why this needs a separate migration

Unlike the static Learning Narrative Kit, this site **generates new HTML every day in GitHub Actions** using an existing ESV API secret. The output is temporary `_site/index.html`. GitHub owns source and the generator; Cloudflare should serve only that temporary generated page. Do not move the ESV key into JavaScript or a public Worker binding, archive generated Scripture text, or commit `_site/`.

## Reversible deployment sequence

1. Identify the Cloudflare account and check for an existing Worker/Pages project named for this reader. The Cloudflare API read the account identity, but listing projects repeatedly triggered fresh authorization requests. No new Worker or Page was created.
2. Confirm ESV permission for the same public distribution. The existing README flags possible noncompliance with normal ESV storage, display and redistribution terms; a hosting change does not resolve that licensing issue.
3. Configure Cloudflare CI access in GitHub Actions with `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` secrets (never in source). Keep the existing `ESV_API_KEY` secret unchanged. Authenticate a Cloudflare CLI session or authorized agent for the *first* deployment; run `npm run cloudflare:deploy` only after `python generate_page.py` has produced `_site/index.html`.
4. Record and browser-verify the actual Cloudflare URL, then set GitHub repository variable `CLOUDFLARE_READING_URL` to that exact address. Set `CLOUDFLARE_DUAL_PUBLISH=true` **only then**. The unchanged nightly job will continue publishing and verifying GitHub Pages, then deploy and verify the same ephemeral HTML to Cloudflare using `verify_live.py` (today's Boise date, four readings, attribution, and byte-for-byte equivalence).
5. Observe several real midnight/DST transitions. Confirm the existing backup automation checks the correct new live URL before retiring Pages. When validated, use a separate PR to remove the GitHub Pages upload/deploy steps and unnecessary Pages permissions; keep the tests, Boise schedule, no-text-retention protections, and error behavior.

This draft deliberately leaves Cloudflare dual-publication **off** and does not alter the existing nightly Pages output or backup dispatch logic. The monthly empty GitHub commit remains, because the schedule still runs there after hosting changes. The `_site/` and `.cloudflare/` directories remain ignored.

## Useful commands

```bash
python -m unittest discover -s tests -v
# With an authorized ESV_API_KEY, only after `python generate_page.py`:
npm run cloudflare:dry-run
# Authenticated Cloudflare publication, after checking for an existing project:
npm run cloudflare:deploy
```

Official references: [Cloudflare `cf` static directory deployment](https://developers.cloudflare.com/cf/projects/#deploy-a-static-assets-directory), [Workers Static Assets](https://developers.cloudflare.com/workers/static-assets/index.md).
