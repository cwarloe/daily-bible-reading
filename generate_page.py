"""Generate today's reader-friendly M'Cheyne ESV reading page."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


ROOT = Path(__file__).resolve().parent
PLAN_PATH = ROOT / "mcheyne.json"
OUTPUT_PATH = ROOT / "_site" / "index.html"
ESV_ENDPOINT = "https://api.esv.org/v3/passage/text/"
BOISE = ZoneInfo("America/Boise")


def target_date(value: str | None = None) -> date:
    """Return an explicit ISO date or today's date in Boise."""
    if value:
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("TARGET_DATE must use YYYY-MM-DD format") from exc
    return datetime.now(BOISE).date()


def schedule_key(reading_date: date) -> str:
    """Map a calendar date to the 365-day plan, repeating Feb. 28 on leap day."""
    key = reading_date.strftime("%m-%d")
    return "02-28" if key == "02-29" else key


def load_plan(path: Path = PLAN_PATH) -> dict[str, dict[str, list[str]]]:
    with path.open(encoding="utf-8") as source:
        plan = json.load(source)
    if len(plan) != 365:
        raise ValueError(f"Expected 365 calendar entries; found {len(plan)}")
    expected = {(date(2025, 1, 1) + timedelta(days=i)).strftime("%m-%d") for i in range(365)}
    if set(plan) != expected:
        raise ValueError("Schedule must contain every non-leap calendar date")
    for key, day in plan.items():
        if set(day) != {"family", "private"} or any(
            not isinstance(refs, list) or len(refs) != 2 or
            any(not isinstance(ref, str) or not ref.strip() for ref in refs)
            for refs in day.values()
        ):
            raise ValueError(f"Invalid reading entry: {key}")
    return plan


def fetch_passage(session: requests.Session, api_key: str, reference: str) -> str:
    response = session.get(
        ESV_ENDPOINT,
        headers={"Authorization": f"Token {api_key}"},
        params={
            "q": reference,
            "include-passage-references": "false",
            "include-verse-numbers": "false",
            "include-first-verse-numbers": "false",
            "include-footnotes": "false",
            "include-footnote-body": "false",
            "include-headings": "true",
            "include-short-copyright": "false",
            "include-copyright": "false",
            "include-passage-horizontal-lines": "false",
            "include-heading-horizontal-lines": "false",
            "line-length": "0",
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    passages = payload.get("passages", [])
    if not isinstance(passages, list) or not all(isinstance(part, str) for part in passages):
        raise RuntimeError(f"Invalid ESV response for {reference}")
    text = "\n\n".join(part.strip() for part in passages if part.strip()).strip()
    if not text:
        raise RuntimeError(f"The ESV API returned no text for {reference}")
    return text


def text_to_html(text: str) -> str:
    """Preserve paragraphs and poetry without modifying the ESV words."""
    blocks = re.split(r"\n\s*\n", text.strip())
    rendered = []
    for block in blocks:
        lines = [html.escape(line.strip()) for line in block.splitlines() if line.strip()]
        if lines:
            rendered.append(f"<p>{'<br>'.join(lines)}</p>")
    return "\n".join(rendered)


def reading_section(title: str, references: list[str], texts: list[str]) -> str:
    passages = []
    for reference, text in zip(references, texts, strict=True):
        passages.append(
            f'''<section class="passage">
        <h2>{html.escape(reference)}</h2>
        {text_to_html(text)}
      </section>'''
        )
    return f'''<section class="reading">
      <h2>{html.escape(title)}</h2>
      {''.join(passages)}
    </section>'''


def render_page(reading_date: date, plan: dict[str, list[str]], texts: dict[str, list[str]]) -> str:
    readable_date = f"{reading_date:%A, %B} {reading_date.day}, {reading_date.year}"
    morning = reading_section("Morning — Family Reading", plan["family"], texts["family"])
    evening = reading_section("Evening — Private Reading", plan["private"], texts["private"])
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="reading-date" content="{reading_date.isoformat()}">
  <meta name="description" content="Today's M'Cheyne Bible readings in the ESV">
  <title>M’Cheyne Bible Reading — {html.escape(readable_date)}</title>
  <style>
    :root {{ color-scheme: light; --ink:#20201d; --muted:#67675f; --rule:#deddd5; --paper:#fffefa; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--paper); color:var(--ink); font:1.15rem/1.72 Georgia, 'Times New Roman', serif; }}
    main {{ width:min(46rem, calc(100% - 2rem)); margin:0 auto; padding:2.5rem 0 4rem; }}
    .document-title {{ margin:0; font-size:clamp(1.75rem, 6vw, 2.6rem); line-height:1.15; }}
    .date {{ margin:.45rem 0 3rem; color:var(--muted); }}
    .reading {{ margin:0 0 4rem; }}
    .reading > h2 {{ padding-bottom:.45rem; border-bottom:2px solid var(--ink); font-size:1.65rem; }}
    .passage {{ margin:2.5rem 0 3.25rem; }}
    .passage h2 {{ margin:0 0 1.2rem; font-size:1.35rem; }}
    p {{ margin:0 0 1.15rem; }}
    footer {{ padding-top:1.5rem; border-top:1px solid var(--rule); color:var(--muted); font:0.78rem/1.5 system-ui,sans-serif; }}
    footer a {{ color:inherit; }}
    @media (max-width:35rem) {{ body {{ font-size:1.08rem; }} main {{ padding-top:1.5rem; }} }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1 class="document-title">M’Cheyne Bible Reading</h1>
      <p class="date">{html.escape(readable_date)}</p>
    </header>
    {morning}
    {evening}
    <footer>
      <p>Scripture quotations are from the ESV® Bible (The Holy Bible, English Standard Version®), © 2001 by Crossway, a publishing ministry of Good News Publishers. Used by permission. All rights reserved. The ESV text may not be quoted in any publication made available to the public by a Creative Commons license. The ESV may not be translated into any other language.</p>
      <p>Users may not copy or download more than 500 verses of the ESV Bible or more than one half of any book of the ESV Bible. <a href="https://www.esv.org/">ESV.org</a></p>
    </footer>
  </main>
</body>
</html>
'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Generate a specific date (YYYY-MM-DD)")
    args = parser.parse_args()

    api_key = os.environ.get("ESV_API_KEY")
    if not api_key:
        print("ESV_API_KEY is required", file=sys.stderr)
        return 2

    reading_date = target_date(args.date or os.environ.get("TARGET_DATE"))
    key = schedule_key(reading_date)
    annual_plan = load_plan()
    if key not in annual_plan:
        raise KeyError(f"No M'Cheyne reading found for {key}")
    plan = annual_plan[key]

    texts: dict[str, list[str]] = {"family": [], "private": []}
    with requests.Session() as session:
        session.mount("https://", HTTPAdapter(max_retries=Retry(
            total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )))
        for track in texts:
            texts[track] = [fetch_passage(session, api_key, ref) for ref in plan[track]]

    page = render_page(reading_date, plan, texts)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT_PATH.with_suffix(".html.tmp")
    temporary.write_text(page, encoding="utf-8")
    temporary.replace(OUTPUT_PATH)
    print(f"Generated {OUTPUT_PATH.name} for {reading_date.isoformat()}: "
          f"{', '.join(plan['family'] + plan['private'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
