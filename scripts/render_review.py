"""Render source-backed Chinese paper articles with interleaved figures and a concise closing."""
import argparse
from validate_record import load_records, validate_record, digest
import json
import os
import re
import sys
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile

import pypdfium2 as pdfium
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

WIDTH, MARGIN = 500, 36
COLUMN = WIDTH - 2 * MARGIN
INK, MUTED, RED = '#242B31', '#58616B', '#AC392F'
BODY = 'Body'
HEADING = 'Heading'


def install_fonts(body=None, heading=None):
    body_file = body or os.getenv('CJK_FONT')
    if not body_file:
        candidates = [
            '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
            'C:/Windows/Fonts/msyh.ttc',
        ]
        body_file = next((x for x in candidates if Path(x).is_file()), None)
    if not body_file or not Path(body_file).is_file():
        raise ValueError('Set --body-font or CJK_FONT to a CJK TrueType font; no usable default found')
    head_file = heading or os.getenv('CJK_HEADING_FONT')
    if not head_file:
        mac = '/System/Library/Fonts/Supplemental/Songti.ttc'
        head_file = mac if Path(mac).is_file() else body_file
    pdfmetrics.registerFont(TTFont(BODY, body_file))
    pdfmetrics.registerFont(TTFont(HEADING, head_file))
    # Fail before generating unreadable Chinese. CFF outlines may also fail registration.
    for font in (BODY, HEADING):
        cmap = pdfmetrics.getFont(font).face.charToGlyph
        if any(ord(char) not in cmap for char in '论文研究模型阴影'):
            raise ValueError(f'{font}: font lacks common Chinese glyphs')
    return {'body': str(body_file), 'heading': str(head_file)}


def wrap(text, width, font, size):
    lines, current = [], ''
    # Keep Latin model names and numbers legible, and punctuation with its preceding character.
    tokens = re.findall(r"[A-Za-z0-9]+(?:[.,’'/-][A-Za-z0-9]+)*|.", text)
    for token in tokens:
        if pdfmetrics.stringWidth(token, font, size) > width:
            if current:
                lines.append(current.rstrip()); current = ''
            for char in token:
                if current and pdfmetrics.stringWidth(current + char, font, size) > width:
                    lines.append(current); current = ''
                current += char
            continue
        if current and pdfmetrics.stringWidth(current + token, font, size) > width:
            if token in '。，、？！）》」%；':
                previous = current[-1:]
                lines.append(current[:-1].rstrip())
                current = previous + token
            else:
                lines.append(current.rstrip())
                current = token.lstrip()
        else:
            current += token
    return lines + [current.rstrip()] if current else lines


def source_figure(document, figure):
    page = document[figure['page'] - 1]
    width, height = page.get_size()
    left, top, right, bottom = figure['box']
    crop = (left * width, (1 - bottom) * height, (1 - right) * width, top * height)
    bitmap = page.render(scale=3.7, crop=crop)
    try:
        return bitmap.to_pil().convert('RGB')
    finally:
        bitmap.close()
        page.close()


class ArticlePage:
    """Measure the article column before drawing so that captions and explanations stay together."""
    def __init__(self):
        self.items = []
        self.y = 32

    def text(self, text, font=BODY, size=12.1, leading=21, color=INK, after=14):
        for line in wrap(text, COLUMN, font, size):
            self.items.append(('text', MARGIN, self.y + size, line, font, size, color))
            self.y += leading
        self.y += after

    def heading(self, text):
        self.items.append(('bar', self.y + 1))
        for line in wrap(text, COLUMN - 11, HEADING, 15.5):
            self.items.append(('text', MARGIN + 11, self.y + 15, line, HEADING, 15.5, RED))
            self.y += 23
        self.y += 7

    def append(self, block):
        offset = self.y
        for kind, *values in block.items:
            values[0 if kind == 'bar' else 1] += offset
            self.items.append((kind, *values))
        self.y += block.y

    def figure(self, image, label, max_height=350):
        scale = min(COLUMN / image.width, max_height / image.height)
        width, height = image.width * scale, image.height * scale
        self.y += 1
        self.items.append(('image', (WIDTH-width)/2, self.y, image, width, height))
        self.y += height + 6
        self.text(label, BODY, 9.3, 14, MUTED, 8)

    def draw(self, canvas, record, page_number, total_pages):
        height = self.y + 31
        if height > 1440:
            raise ValueError('Page exceeds 1440 pt: shorten prose or split exhibits before rendering')
        canvas.setPageSize((WIDTH, height))
        for kind, *values in self.items:
            if kind == 'text':
                x, y, line, font, size, color = values
                canvas.setFillColor(HexColor(color))
                canvas.setFont(font, size)
                canvas.drawString(x, height-y, line)
                if line.startswith('DOI  '):
                    canvas.linkURL('https://doi.org/'+record['doi'],
                                   (x, height-y-2, x+pdfmetrics.stringWidth(line,font,size), height-y+size))
            elif kind == 'image':
                x, y, image, width, h = values
                canvas.drawImage(ImageReader(image), x, height-y-h, width, h)
            elif kind == 'bar':
                canvas.setFillColor(HexColor(RED))
                canvas.rect(MARGIN, height-values[0]-16, 3, 16, fill=1, stroke=0)
        canvas.setStrokeColor(HexColor('#D9D9D7'))
        canvas.line(MARGIN, 32, WIDTH-MARGIN, 32)
        canvas.setFillColor(HexColor(MUTED))
        canvas.setFont(BODY, 8)
        canvas.drawString(MARGIN, 16, (record.get('series', '')+'  /  ' if record.get('series') else '')+'论文图解   '+record['id'])
        canvas.drawRightString(WIDTH-MARGIN, 16, f"{page_number} / {total_pages}")
        canvas.showPage()


def generate_legacy(record, papers, output):
    article, technical, editorial = record['article'], record['technical'], record['wechat']
    performance = technical.get('performance', [])
    target = output / f"{record['id']} {record['topic']}.pdf"
    pages = []
    with pdfium.PdfDocument(papers / record['source']) as original:
        validate_record(record, page_count=len(original))
        page = ArticlePage()
        page.text(record['journal']+'   /   论文图解', BODY, 10, 14, RED, 11)
        page.text(article['headline'], HEADING, 23, 31, INK, 10)
        title_font = BODY if any(ord(c) >= 0x3000 for c in record['title']) else 'Helvetica-Oblique'
        page.text(record['title'], title_font, 10, 14, MUTED, 7)
        page.text(article['byline'], BODY, 9.6, 14, MUTED, 3)
        if record.get('doi'):
            page.text('DOI  '+record['doi'], 'Helvetica', 9, 12, RED, 17)
        page.heading('01   研究从什么问题出发')
        page.text(editorial['problem'])
        page.heading('02   方法如何解决问题')
        page.text(editorial['method'])
        if article['figures']:
            figure = article['figures'][0]
            page.figure(source_figure(original, figure),
                        f"原文{figure['number']} · PDF 第 {figure['page']} 页｜"+article['caption1'], max_height=430)
            page.text('读图：'+article['guide1'], size=11, leading=18, color=MUTED, after=8)
        else:
            page.text('原文未提供技术路线图：'+article['route_missing_reason'], size=11, leading=18, color=MUTED)
        pages.append(page)

        page = ArticlePage()
        page.text(record['journal']+'   /   模型与实验结果', BODY, 10, 14, RED, 13)
        if len(article['figures']) > 1:
            figure = article['figures'][1]
            # Performance tables already shown below should not appear twice.
            if not any((x['number'], x['page']) == (figure['number'], figure['page']) for x in performance):
                page.heading('原文图解｜方法与研究对象')
                page.figure(source_figure(original, figure),
                            f"原文{figure['number']} · PDF 第 {figure['page']} 页｜"+article['caption2'], max_height=420)
                page.text('读图：'+article['guide2'], size=11, leading=18, color=MUTED)
        page.heading('03   实验结果说明了什么')
        page.text(editorial['result'], size=11.7, leading=20, after=10)
        page.text('数值沿用论文设置。原文定位：'+technical['location'],
                  size=9, leading=14, color=MUTED, after=5)
        pages.append(page)

        # Keep all original performance exhibits, group short tables on the same page.
        heading = technical.get('performance_heading', '原文性能图表')
        page = None
        count = 0
        for exhibit in performance:
            block = ArticlePage()
            block.y = 0
            block.text(exhibit['title'], HEADING, 14, 21, INK, 8)
            block.figure(source_figure(original, exhibit),
                         f"原文{exhibit['number']} · PDF 第 {exhibit['page']} 页", max_height=650)
            block.text('读图：'+exhibit['guide'], size=11, leading=18, color=MUTED, after=18)
            if page is None or (count and page.y + block.y > 900):
                if page is not None:
                    pages.append(page)
                page = ArticlePage()
                page.text(record['journal']+'   /   实验依据', BODY, 10, 14, RED, 11)
                page.heading(heading)
                if record.get('kind') == 'review':
                    page.text('本文是综述。下列为原文汇总材料，不代表作者训练了统一对比模型。', size=10.5, leading=17, color=MUTED, after=13)
                count = 0
            offset = page.y
            for kind, *values in block.items:
                if kind in ('image','text'):
                    values[1] += offset
                elif kind == 'bar':
                    values[0] += offset
                page.items.append((kind, *values))
            page.y += block.y
            count += 1
        if page is not None:
            pages.append(page)
        if not performance:
            page = ArticlePage()
            page.heading('原文性能证据说明')
            page.text(technical['performance_missing_reason'])
            pages.append(page)

    page = ArticlePage()
    page.text(record['journal']+'   /   方法借鉴', BODY, 10, 14, RED, 11)
    page.heading('04   我们可以从这篇论文中学到什么')
    for index, item in enumerate(editorial['conclusion'], 1):
        page.text(f"{index}. {item['title']}", HEADING, 13.5, 21, RED, 5)
        page.text(item['text'], size=11.7, leading=20, after=15)
    evidence_note = '。图表及原文页码见前页。' if article['figures'] or performance else '。原文未提供对应图表。'
    page.text('原文依据：'+record['reference']+evidence_note, size=9, leading=14, color=MUTED, after=7)
    pages.append(page)

    stream = BytesIO()
    canvas = Canvas(stream, pageCompression=1)
    canvas.setTitle(article['headline'])
    canvas.setSubject(record['title'])
    canvas.setAuthor((record.get('series', '')+' · ' if record.get('series') else '')+'论文图解')
    for i, page in enumerate(pages, 1):
        page.draw(canvas, record, i, len(pages))
    canvas.save()
    with NamedTemporaryFile(dir=output, suffix='.tmp', delete=False) as temporary:
        temporary.write(stream.getvalue())
    os.replace(temporary.name, target)
    print(f"{target.name}  [{len(pages)} 页]")
    return {"id": record["id"], "output": target.name, "pages": len(pages), "performance_exhibits": len(performance), "source_sha256": digest(papers / record["source"]), "record_sha256": __import__("hashlib").sha256(json.dumps(record, ensure_ascii=False, sort_keys=True).encode()).hexdigest(), "output_sha256": digest(target)}


def narrative_pages(record, original):
    """Keep each exhibit with its explanation; break at paragraphs, never force a closing page."""
    article, technical, narrative = record['article'], record['technical'], record['narrative']
    pages = []
    page = ArticlePage()
    page.text(record['journal']+'   /   论文图解', BODY, 10, 14, RED, 11)
    page.text(article['headline'], HEADING, 23, 31, INK, 10)
    title_font = BODY if any(ord(c) >= 0x3000 for c in record['title']) else 'Helvetica-Oblique'
    page.text(record['title'], title_font, 10, 14, MUTED, 7)
    page.text(article['byline'], BODY, 9.6, 14, MUTED, 3)
    if record.get('doi'):
        page.text('DOI  '+record['doi'], 'Helvetica', 9, 12, RED, 17)

    def block():
        item = ArticlePage()
        item.y = 0
        return item

    def add(item, limit=1000):
        nonlocal page
        if item.y > 820:
            raise ValueError('Narrative block too tall: split long prose or divide the original exhibit into labeled parts')
        if page.y + item.y > limit:
            pages.append(page)
            page = ArticlePage()
            page.text(record['journal']+'   /   论文图解', BODY, 10, 14, RED, 11)
        page.append(item)

    for section in narrative['sections']:
        chunks = []
        for i, paragraph in enumerate(section['paragraphs']):
            item = block()
            if i == 0:
                item.heading(section['heading'])
            item.text(paragraph)
            chunks.append(item)
        for index in section.get('figure_indices', []):
            figure = article['figures'][index-1]
            item = block()
            item.figure(source_figure(original, figure),
                        f"原文{figure['number']} · PDF 第 {figure['page']} 页｜"+figure['caption'], max_height=480)
            item.text(figure['guide'], size=11, leading=18, color=MUTED, after=20)
            chunks.append(item)
        # Short method sections stay intact so the explanation and its source figure are adjacent.
        whole = block()
        for item in chunks:
            whole.append(item)
        if whole.y <= 820:
            add(whole)
        else:
            for item in chunks:
                add(item)
    if not article['figures']:
        item = block()
        item.text('原文路线/机制图说明：'+article['route_missing_reason'], size=10.5, leading=17, color=MUTED)
        add(item)

    for i, paragraph in enumerate(narrative['result_paragraphs']):
        item = block()
        if i == 0:
            item.heading(narrative['result_heading'])
        item.text(paragraph)
        add(item)
    performance = technical.get('performance', [])
    for exhibit in performance:
        item = block()
        item.text(exhibit['title'], HEADING, 13.5, 21, INK, 8)
        for paragraph in exhibit.get('paragraphs', []):
            item.text(paragraph)
        item.figure(source_figure(original, exhibit),
                    f"原文{exhibit['number']} · PDF 第 {exhibit['page']} 页", max_height=620)
        item.text(exhibit['guide'], size=11, leading=18, color=MUTED, after=20)
        add(item)
    if not performance:
        item = block()
        item.text('原文性能证据说明：'+technical['performance_missing_reason'], size=10.5, leading=17, color=MUTED)
        add(item)

    item = block()
    item.heading('结语')
    item.text(narrative['closing'])
    item.text('原文依据：'+record['reference'],
              size=9, leading=14, color=MUTED, after=7)
    # A short closing may extend the final screen-oriented page instead of becoming an isolated page.
    add(item, limit=1120)
    pages.append(page)
    return pages


def generate(record, papers, output):
    if record.get('schema_version', 1) == 1:
        return generate_legacy(record, papers, output)
    target = output / f"{record['id']} {record['topic']}.pdf"
    with pdfium.PdfDocument(papers / record['source']) as original:
        validate_record(record, page_count=len(original))
        pages = narrative_pages(record, original)
    stream = BytesIO()
    canvas = Canvas(stream, pageCompression=1)
    canvas.setTitle(record['article']['headline'])
    canvas.setSubject(record['title'])
    canvas.setAuthor((record.get('series', '')+' · ' if record.get('series') else '')+'论文图解')
    for i, page in enumerate(pages, 1):
        page.draw(canvas, record, i, len(pages))
    canvas.save()
    with NamedTemporaryFile(dir=output, suffix='.tmp', delete=False) as temporary:
        temporary.write(stream.getvalue())
    os.replace(temporary.name, target)
    print(f"{target.name}  [{len(pages)} 页]")
    return {'id': record['id'], 'output': target.name, 'pages': len(pages),
            'performance_exhibits': len(record['technical'].get('performance', [])),
            'source_sha256': digest(papers / record['source']),
            'record_sha256': __import__('hashlib').sha256(json.dumps(record, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
            'output_sha256': digest(target)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--papers', required=True, type=Path, help='Original paper folder')
    parser.add_argument('--records', required=True, type=Path, help='Curated JSON folder')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--ids', nargs='+', help='Only render these IDs; otherwise render all')
    parser.add_argument('--body-font')
    parser.add_argument('--heading-font')
    args = parser.parse_args()
    try:
        records = load_records(args.records, args.papers, args.ids)
        fonts = install_fonts(args.body_font, args.heading_font)
        # Check every Chinese/Latin character used by the two embedded fonts.
        for record in records:
            prose = json.dumps(record, ensure_ascii=False)
            for font in (BODY, HEADING):
                cmap = pdfmetrics.getFont(font).face.charToGlyph
                missing = {c for c in prose if ord(c) >= 0x3000 and ord(c) not in cmap}
                if missing:
                    raise ValueError(f"{record['id']} {font}: unsupported characters {''.join(sorted(missing))}")
        sources = {(args.papers / r['source']).resolve() for r in records}
        for record in records:
            target = args.output / f"{record['id']} {record['topic']}.pdf"
            if target.resolve() in sources:
                raise ValueError('Output would overwrite an original PDF; use a separate output directory')
        args.output.mkdir(parents=True, exist_ok=True)
        results = [generate(r, args.papers, args.output) for r in records]
        manifest = {'renderer_sha256': digest(__file__), 'fonts': fonts, 'outputs': results}
        (args.output/'render_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        known = {json.loads(p.read_text(encoding='utf-8'))['source'] for p in args.records.glob('*.json')}
        for source in sorted(args.papers.glob('*.pdf')):
            if source.name not in known:
                print('待整理原文:', source.name)
    except (KeyError, ValueError, OSError) as error:
        parser.exit(1, str(error)+'\n')


if __name__ == '__main__':
    main()
