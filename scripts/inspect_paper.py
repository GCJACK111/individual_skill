"""Inventory sources, extract page-located text, preview pages, or render original crops."""
from contextlib import closing
import argparse
import json
from pathlib import Path
import pypdfium2 as pdfium
from PIL import ImageDraw
from validate_record import digest, validate_exhibit


def render(page, scale=1.5, box=None):
    crop = (0, 0, 0, 0)
    if box:
        w, h = page.get_size(); l, t, r, b = box
        crop = (l*w, (1-b)*h, (1-r)*w, t*h)
    bitmap = page.render(scale=scale, crop=crop)
    try:
        return bitmap.to_pil().convert('RGB')
    finally:
        bitmap.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    inv = subs.add_parser('inventory')
    inv.add_argument('--papers', required=True, type=Path)
    inv.add_argument('--records', type=Path)
    inspect = subs.add_parser('inspect')
    inspect.add_argument('--pdf', required=True, type=Path)
    inspect.add_argument('--out', required=True, type=Path)
    preview = subs.add_parser('preview')
    preview.add_argument('--pdf', required=True, type=Path)
    preview.add_argument('--pages', required=True, type=int, nargs='+')
    preview.add_argument('--out', required=True, type=Path)
    preview.add_argument('--grid', action='store_true')
    crop = subs.add_parser('crop')
    crop.add_argument('--pdf', required=True, type=Path)
    crop.add_argument('--page', required=True, type=int)
    crop.add_argument('--box', required=True, nargs=4, type=float)
    crop.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    if args.command == 'inventory':
        existing = {}
        if args.records:
            for path in args.records.glob('*.json'):
                d = json.loads(path.read_text(encoding='utf-8')); existing[d['source']] = d['id']
        hashes = {}
        for path in sorted(args.papers.glob('*.pdf')):
            checksum = digest(path)
            row = {'source': path.name, 'sha256': checksum, 'record_id': existing.get(path.name), 'same_bytes_as': hashes.get(checksum)}
            print(json.dumps(row, ensure_ascii=False)); hashes[checksum] = path.name
        return
    with pdfium.PdfDocument(args.pdf) as doc:
        if args.command == 'inspect':
            args.out.mkdir(parents=True, exist_ok=True)
            metadata = {'filename': args.pdf.name, 'sha256': digest(args.pdf), 'pages': len(doc), 'page_sizes': []}
            all_text = []
            for i in range(len(doc)):
                with closing(doc[i]) as page:
                    with closing(page.get_textpage()) as textpage:
                        text = textpage.get_text_bounded()
                    metadata['page_sizes'].append(list(page.get_size()))
                    (args.out/f'page-{i+1:03}.txt').write_text(text, encoding='utf-8')
                    all_text.append(f'\n=== PDF PAGE {i+1} ===\n{text}')
            (args.out/'full.txt').write_text(''.join(all_text), encoding='utf-8')
            (args.out/'source.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
            print(f'Extracted {len(doc)} pages; visually inspect method, result, appendix and caption pages')
        elif args.command == 'preview':
            args.out.mkdir(parents=True, exist_ok=True)
            for n in args.pages:
                if not 1 <= n <= len(doc):
                    raise ValueError(f'Invalid 1-based page: {n}')
                with closing(doc[n-1]) as page:
                    im = render(page)
                if args.grid:
                    draw = ImageDraw.Draw(im)
                    for i in range(1, 10):
                        x, y = round(im.width*i/10), round(im.height*i/10)
                        draw.line((x,0,x,im.height), fill='#cc5555', width=1)
                        draw.line((0,y,im.width,y), fill='#cc5555', width=1)
                        draw.text((x+3,3), str(i/10), fill='#bb2222')
                        draw.text((3,y+3), str(i/10), fill='#bb2222')
                im.save(args.out/f'page-{n:03}.png')
        else:
            validate_exhibit({'page': args.page, 'box': args.box, 'number': 'preview'}, 'crop', len(doc))
            with closing(doc[args.page-1]) as page:
                im = render(page, 3.7, args.box)
            args.out.parent.mkdir(parents=True, exist_ok=True); im.save(args.out)


if __name__ == '__main__':
    main()
