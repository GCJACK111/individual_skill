"""Validate editorial records and source identity before rendering (stdlib only)."""
import hashlib
import json
from pathlib import Path


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def required_text(obj, key, context):
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{context}.{key}: expected nonempty text')
    return value


def validate_exhibit(exhibit, context, page_count=None):
    if not isinstance(exhibit, dict):
        raise ValueError(f'{context}: expected an object')
    n = exhibit.get('page')
    if type(n) is not int or n < 1 or (page_count is not None and n > page_count):
        raise ValueError(f'{context}.page: expected a valid 1-based PDF page')
    required_text(exhibit, 'number', context)
    box = exhibit.get('box')
    if not isinstance(box, list) or len(box) != 4 or any(type(v) not in (int, float) for v in box):
        raise ValueError(f'{context}.box: expected [left, top, right, bottom]')
    l, t, r, b = box
    if not (0 <= l < r <= 1 and 0 <= t < b <= 1):
        raise ValueError(f'{context}.box: coordinates must be ordered and within [0, 1]')


def validate_record(record, papers=None, page_count=None):
    for key in ('id', 'topic', 'source', 'title', 'journal', 'reference'):
        required_text(record, key, 'record')
    for key in ('id', 'topic'):
        if any(c in record[key] for c in '/\\\x00') or record[key] in ('.', '..'):
            raise ValueError(f'record.{key}: unsafe output filename')
    if record.get('kind', 'research') not in ('research', 'review'):
        raise ValueError('record.kind: expected research or review')
    a, w, tech = record['article'], record['wechat'], record['technical']
    for key in ('headline', 'byline'):
        required_text(a, key, 'article')
    figures = a.get('figures', [])
    if len(figures) > 2:
        raise ValueError('article.figures: only route and model slots are rendered; put extra evidence in technical.performance')
    if not figures:
        required_text(a, 'route_missing_reason', 'article')
    for i, exhibit in enumerate(figures, 1):
        validate_exhibit(exhibit, f'article.figures[{i-1}]', page_count)
        for prefix in ('caption', 'guide'):
            required_text(a, f'{prefix}{i}', 'article')
    for key in ('problem', 'method', 'result'):
        required_text(w, key, 'wechat')
    conclusions = w.get('conclusion', [])
    if not isinstance(conclusions, list) or not 3 <= len(conclusions) <= 5:
        raise ValueError('wechat.conclusion: expected 3 to 5 concrete takeaways')
    for i, item in enumerate(conclusions):
        for key in ('title', 'text'):
            required_text(item, key, f'wechat.conclusion[{i}]')
    required_text(tech, 'location', 'technical')
    performance = tech.get('performance', [])
    if not performance:
        required_text(tech, 'performance_missing_reason', 'technical')
    for i, exhibit in enumerate(performance):
        validate_exhibit(exhibit, f'technical.performance[{i}]', page_count)
        for key in ('title', 'guide'):
            required_text(exhibit, key, f'technical.performance[{i}]')
    if papers is not None:
        root = Path(papers).resolve()
        source = (root / record['source']).resolve()
        if not source.is_relative_to(root) or source.suffix.lower() != '.pdf':
            raise ValueError('source must be a PDF within --papers')
        if not source.is_file():
            raise FileNotFoundError(f'Missing original PDF: {source}')
        expected = record.get('source_sha256')
        if expected and digest(source) != expected:
            raise ValueError(f"{record['id']}: original PDF changed; recheck pages/crops before updating source_sha256")


def load_records(directory, papers=None, ids=None):
    records, seen_ids, seen_dois, seen_sources = [], set(), set(), set()
    for path in sorted(Path(directory).glob('*.json')):
        record = json.loads(path.read_text(encoding='utf-8'))
        # Validate the full inventory, but only require source PDFs for selected records.
        selected = not ids or record.get('id') in ids
        validate_record(record, papers if selected else None)
        doi = record.get('doi', '').strip().lower().removeprefix('https://doi.org/')
        if record['id'] in seen_ids or (doi and doi in seen_dois) or record['source'] in seen_sources:
            raise ValueError(f'Duplicate ID, DOI, or source in {path}')
        seen_ids.add(record['id']); seen_sources.add(record['source'])
        if doi:
            seen_dois.add(doi)
        if selected:
            records.append(record)
    if ids and set(ids) - seen_ids:
        raise ValueError(f'Unknown IDs: {sorted(set(ids) - seen_ids)}')
    if not records:
        raise ValueError('No reviewed records selected; author JSON records before rendering')
    return records


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--records', required=True, type=Path)
    parser.add_argument('--papers', type=Path)
    parser.add_argument('--ids', nargs='+')
    args = parser.parse_args()
    try:
        records = load_records(args.records, args.papers, args.ids)
        print(f'Validated {len(records)} editorial records')
    except (KeyError, ValueError, OSError) as error:
        parser.exit(1, str(error)+'\n')
