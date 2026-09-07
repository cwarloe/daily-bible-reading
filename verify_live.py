"""Verify the deployed HTML without logging or archiving Scripture text."""
import html
import os
import time
from pathlib import Path
import requests
from generate_page import load_plan, schedule_key, target_date


def verify(page, reading_date):
    if f'<meta name="reading-date" content="{reading_date.isoformat()}">' not in page:
        raise ValueError('Published date is incorrect')
    for ref in sum(load_plan()[schedule_key(reading_date)].values(), []):
        if f'<h2>{html.escape(ref)} ' not in page:
            raise ValueError(f'Missing reading: {ref}')
    for required in ['Morning', 'Family Reading', 'Evening', 'Private Reading', 'ESV.org', 'Used by permission.']:
        if required not in page:
            raise ValueError(f'Missing page content: {required}')


def main():
    reading_date = target_date()
    expected = Path('_site/index.html').read_text(encoding='utf-8')
    verify(expected, reading_date)
    url = os.environ['PAGE_URL']
    for attempt in range(18):
        try:
            response = requests.get(url, params={'verify': time.time_ns()}, timeout=20,
                                    headers={'Cache-Control': 'no-cache'})
            response.raise_for_status()
            response.encoding = 'utf-8'
            verify(response.text, reading_date)
            if response.text != expected:
                raise ValueError('Live content does not match the generated page')
            print(f'Verified {url} for {reading_date.isoformat()} and all four readings.')
            return
        except (requests.RequestException, ValueError) as exc:
            if attempt == 17:
                raise RuntimeError('Live page verification failed') from exc
            time.sleep(10)


if __name__ == '__main__':
    main()
