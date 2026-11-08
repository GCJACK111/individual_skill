#!/usr/bin/env python3
"""Export a UTF-8 Markdown summary to a PDF with an embedded Chinese font.

Dependencies: reportlab, markdown-it-py. Tables, lists, links, headings and
fenced code are supported. Images are represented by their alt text and
source (never fetched); LaTeX is retained as readable source, not typeset.
"""
from __future__ import annotations

import argparse
import html
import os
from pathlib import Path
import sys
import tempfile


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path, help='UTF-8 Markdown file')
    parser.add_argument('--output', required=True, type=Path, help='Output PDF file')
    parser.add_argument('--title', help='PDF document title (defaults to first heading)')
    parser.add_argument('--font', type=Path, help='Chinese TrueType font; defaults to bundled Noto Sans SC')
    return parser.parse_args()


def render(source, destination, font_path, title):
    try:
        from markdown_it import MarkdownIt
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, LongTable, TableStyle, HRFlowable
    except ImportError as exc:
        req = Path(__file__).resolve().parent.parent / 'requirements.txt'
        raise RuntimeError(
            f'Missing Python dependency: {exc.name}. Use your Python environment to run '
            f'python -m pip install -r "{req}", then retry with that same Python.'
        ) from exc

    font = TTFont('PaperSC', str(font_path))
    pdfmetrics.registerFont(font)
    bold_path = font_path.with_name(font_path.stem.replace('Regular', 'Bold') + font_path.suffix)
    bold_name = 'PaperSC'
    if bold_path != font_path and bold_path.is_file():
        pdfmetrics.registerFont(TTFont('PaperSCBold', str(bold_path)))
        bold_name = 'PaperSCBold'
    pdfmetrics.registerFontFamily('PaperSC', normal='PaperSC', bold=bold_name, italic='PaperSC', boldItalic=bold_name)

    text = source.read_text(encoding='utf-8-sig')
    if not text.strip():
        raise ValueError('The Markdown input is empty; write the complete summary before exporting.')
    # Refuse silent missing-glyph squares instead of delivering an unreadable PDF.
    all_text = text + (title or '') + '•第页'
    missing = sorted({ord(ch) for ch in all_text if ch.isprintable() and ord(ch) not in font.face.charWidths})
    if missing:
        examples = ', '.join(f'U+{n:04X} {chr(n)!r}' for n in missing[:12])
        raise ValueError(f'Font lacks these characters: {examples}. Use --font with a suitable TrueType font '
                         'or replace unsupported decorative characters with plain text.')

    md = MarkdownIt('commonmark', {'html': False}).enable('table')
    tokens = md.parse(text)
    if not title:
        title = next((tokens[i + 1].content for i, t in enumerate(tokens[:-1]) if t.type == 'heading_open'), source.stem)

    def inline(token):
        pieces, links = [], []
        for child in token.children or []:
            kind = child.type
            if kind == 'text':
                pieces.append(html.escape(child.content))
            elif kind in ('softbreak', 'hardbreak'):
                pieces.append('<br/>')
            elif kind == 'code_inline':
                pieces.append('<font color="#334155">' + html.escape(child.content) + '</font>')
            elif kind in ('strong_open', 'strong_close', 'em_open', 'em_close'):
                pieces.append({'strong_open': '<b>', 'strong_close': '</b>', 'em_open': '<i>', 'em_close': '</i>'}[kind])
            elif kind == 'link_open':
                href = child.attrGet('href') or ''
                enabled = href.lower().startswith(('http://', 'https://', 'mailto:'))
                links.append(enabled)
                if enabled:
                    pieces.append('<a href="' + html.escape(href, quote=True) + '" color="#1d4ed8">')
            elif kind == 'link_close':
                if links and links.pop():
                    pieces.append('</a>')
            elif kind == 'image':
                alt, src = child.content or '未提供说明', child.attrGet('src') or ''
                pieces.append(html.escape(f'【图片：{alt}；来源：{src}】'))
            else:
                pieces.append(html.escape(child.content or ''))
        return ''.join(pieces) or '&#160;'

    width, height = A4
    margin = 46
    body_width = width - 2 * margin
    styles = {}
    styles['body'] = ParagraphStyle('body', fontName='PaperSC', fontSize=10.5, leading=17,
                                    wordWrap='CJK', splitLongWords=True, spaceAfter=7,
                                    textColor=colors.HexColor('#172033'))
    for level, size in [(1, 21), (2, 16), (3, 13), (4, 11.5), (5, 11), (6, 10.5)]:
        styles[f'h{level}'] = ParagraphStyle(f'h{level}', parent=styles['body'], fontName=bold_name,
                                            fontSize=size, leading=size * 1.4, spaceBefore=12,
                                            spaceAfter=7, keepWithNext=True,
                                            textColor=colors.HexColor('#123b5d'))
    styles['code'] = ParagraphStyle('code', parent=styles['body'], fontSize=8.5, leading=13,
                                    backColor=colors.HexColor('#f1f5f9'), borderPadding=5,
                                    spaceBefore=2, spaceAfter=2)
    styles['cell'] = ParagraphStyle('cell', parent=styles['body'], fontSize=8.5, leading=13, spaceAfter=0)
    styles['footer'] = ParagraphStyle('footer', parent=styles['body'], fontSize=8, alignment=TA_CENTER)

    story, lists, item_first = [], [], []
    quote_depth, index = 0, 0

    def paragraph(content, style='body', prefix=''):
        left = len(lists) * 14 + quote_depth * 12
        current = ParagraphStyle('nested', parent=styles[style], leftIndent=left)
        story.append(Paragraph(prefix + content, current))

    while index < len(tokens):
        token = tokens[index]
        kind = token.type
        if kind in ('bullet_list_open', 'ordered_list_open'):
            lists.append({'ordered': kind == 'ordered_list_open', 'number': int(token.attrGet('start') or 1)})
        elif kind in ('bullet_list_close', 'ordered_list_close'):
            lists.pop()
        elif kind == 'list_item_open':
            item_first.append(True)
        elif kind == 'list_item_close':
            item_first.pop()
            if lists:
                lists[-1]['number'] += 1
        elif kind == 'blockquote_open':
            quote_depth += 1
        elif kind == 'blockquote_close':
            quote_depth -= 1
        elif kind == 'heading_open':
            paragraph(inline(tokens[index + 1]), token.tag)
            index += 2
        elif kind == 'paragraph_open':
            prefix = ''
            if item_first and item_first[-1] and lists:
                item_first[-1] = False
                prefix = (str(lists[-1]['number']) + '. ' if lists[-1]['ordered'] else '• ')
            paragraph(inline(tokens[index + 1]), prefix=prefix)
            index += 2
        elif kind in ('fence', 'code_block'):
            # One splittable paragraph per line preserves all code while allowing pagination.
            for line in token.content.expandtabs(4).splitlines():
                paragraph(html.escape(line).replace(' ', '&#160;') or '&#160;', 'code')
            story.append(Spacer(1, 7))
        elif kind == 'hr':
            story.append(HRFlowable(width='100%', thickness=0.6, color=colors.HexColor('#b8c8d5'), spaceBefore=8, spaceAfter=8))
        elif kind == 'table_open':
            rows, row = [], []
            while index < len(tokens) and tokens[index].type != 'table_close':
                part = tokens[index]
                if part.type == 'tr_open':
                    row = []
                elif part.type == 'inline':
                    row.append(inline(part))
                elif part.type == 'tr_close':
                    rows.append(row)
                index += 1
            if rows:
                columns = max(map(len, rows))
                if columns > 8:
                    # Very wide tables become labelled records rather than tiny unreadable columns.
                    headers = rows[0]
                    for record in rows[1:]:
                        for col, value in enumerate(record):
                            label = headers[col] if col < len(headers) else str(col + 1)
                            paragraph('<b>' + label + '</b>: ' + value)
                        story.append(Spacer(1, 5))
                else:
                    data = [[Paragraph(value, styles['cell']) for value in row + ['&#160;'] * (columns - len(row))] for row in rows]
                    table = LongTable(data, colWidths=[body_width / columns] * columns,
                                      repeatRows=1, splitByRow=True, splitInRow=True, hAlign='LEFT')
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f0f6')),
                        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#becbd5')),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 5),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                        ('TOPPADDING', (0, 0), (-1, -1), 5),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ]))
                    story.append(table)
                    story.append(Spacer(1, 9))
        index += 1

    pages = 0

    def footer(canvas, doc):
        nonlocal pages
        pages = max(pages, doc.page)
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor('#d4dce3'))
        canvas.line(margin, 34, width - margin, 34)
        canvas.setFont('PaperSC', 8)
        canvas.setFillColor(colors.HexColor('#64748b'))
        canvas.drawCentredString(width / 2, 22, f'第 {doc.page} 页')
        canvas.restoreState()

    doc = SimpleDocTemplate(str(destination), pagesize=A4, leftMargin=margin, rightMargin=margin,
                            topMargin=42, bottomMargin=47, title=title, author='', pageCompression=1)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    if pages == 0 or destination.stat().st_size < 100:
        raise RuntimeError('No pages were generated from this Markdown input.')
    return pages


def main():
    args = arguments()
    source, output = args.input.expanduser().resolve(), args.output.expanduser().resolve()
    font = (args.font or Path(__file__).resolve().parent.parent / 'assets/fonts/NotoSansSC-Regular.ttf').expanduser().resolve()
    temporary = None
    try:
        if not source.is_file():
            raise FileNotFoundError(f'Markdown input does not exist: {source}')
        if output == source:
            raise ValueError('--input and --output must be different files.')
        if output.suffix.lower() != '.pdf':
            raise ValueError('--output must have a .pdf extension.')
        if not font.is_file():
            raise FileNotFoundError(f'Chinese font missing: {font}. Restore the complete skill assets, '
                                    'or supply --font /path/to/Chinese-font.ttf.')
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix='.paper-summary-', suffix='.pdf', dir=output.parent, delete=False) as temp:
            temporary = Path(temp.name)
        pages = render(source, temporary, font, args.title)
        os.replace(temporary, output)
        print(f'PDF generated: {output}\nPages: {pages}\nBytes: {output.stat().st_size}')
        return 0
    except Exception as exc:
        print(f'PDF export failed: {exc}', file=sys.stderr)
        return 1
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


if __name__ == '__main__':
    sys.exit(main())
