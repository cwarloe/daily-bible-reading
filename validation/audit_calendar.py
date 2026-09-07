"""Reproduce the complete comparison with the supplied M'Cheyne PDF.
Run: python -m pip install pypdf; python validation/audit_calendar.py
"""
import calendar
import hashlib
import json
import re
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
BOOKS = ('Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Ruth|1 Samuel|2 Samuel|1 Kings|2 Kings|1 Chronicles|2 Chronicles|Ezra|Nehemiah|Esther|Job|Psalms|Proverbs|Ecclesiastes|Song of Solomon|Isaiah|Jeremiah|Lamentations|Ezekiel|Daniel|Hosea|Joel|Amos|Obadiah|Jonah|Micah|Nahum|Habakkuk|Zephaniah|Haggai|Zechariah|Malachi|Matthew|Mark|Luke|John|Acts|Romans|1 Corinthians|2 Corinthians|Galatians|Ephesians|Philippians|Colossians|1 Thessalonians|2 Thessalonians|1 Timothy|2 Timothy|Titus|Philemon|Hebrews|James|1 Peter|2 Peter|1 John|2 John|3 John|Jude|Revelation').split('|')
LOOKUP = {b.replace(' ', ''): b for b in BOOKS}
LOOKUP.update({'Song': 'Song of Solomon', 'Phillipians': 'Philippians'})
PATTERN = re.compile('|'.join(sorted(LOOKUP, key=len, reverse=True)))

def references(book, spec):
    parts = spec.split(',')
    # Explicitly repeat the book for mixed chapter/verse selections.
    if len(parts) > 1 and ':' in spec:
        return '; '.join(f'{book} {part}' for part in parts)
    if len(parts) > 1 and all(p.isdigit() for p in parts):
        numbers = [int(p) for p in parts]
        if numbers == list(range(numbers[0], numbers[-1]+1)):
            return f'{book} {numbers[0]}-{numbers[-1]}'
        return '; '.join(f'{book} {part}' for part in parts)
    return f'{book} {spec}'

def extract():
    reader = PdfReader(ROOT / 'validation/calendar.pdf')
    plan = {}
    for month in range(1,13):
        day = 0
        for line in reader.pages[month+2].extract_text().splitlines():
            line = re.sub(r'(?<=\d)\s+(?=[123]\s+[A-Za-z])', '|', line)
            compact = re.sub(r'\s+', '', line)
            books = r'\|?(' + PATTERN.pattern + ')'
            spec = r'(\d(?:[\d,:-]*\d)?)'
            row = re.fullmatch(books + spec + books + spec + str(day+1) + books + spec + books + spec, compact)
            if not row:
                continue
            day += 1
            cells = row.groups()
            refs = [references(LOOKUP[cells[i]], cells[i+1]) for i in range(0,8,2)]
            plan[f'{month:02}-{day:02}'] = dict(family=refs[:2], private=refs[2:])
        assert day == calendar.monthrange(2025, month)[1], (month, day)
    return plan

if __name__ == '__main__':
    plan = extract()
    (ROOT / 'validation/calendar-extracted.json').write_text(json.dumps(plan, indent=2)+'\n', encoding='utf-8')
    existing = json.loads((ROOT / 'mcheyne.json').read_text(encoding='utf-8'))
    differences = {key: {'existing': existing[key], 'pdf': value} for key,value in plan.items() if existing[key] != value}
    print('PDF SHA256:', hashlib.sha256((ROOT / 'validation/calendar.pdf').read_bytes()).hexdigest())
    print('Days:',len(plan), 'differing days:',len(differences))
    print(json.dumps(differences, indent=2))

    corrected = json.loads(json.dumps(plan))
    corrected['03-06']['private'][1] = '2 Corinthians 5'
    corrected['05-11']['private'][0] = 'Isaiah 9:8-21; Isaiah 10:1-4'
    assert existing == corrected, 'Undocumented differences from the source calendar'
    print('All 1,460 readings match, allowing only the two documented PDF errata.')
