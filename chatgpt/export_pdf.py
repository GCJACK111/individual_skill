#!/usr/bin/env python3
"""Create a Chinese PDF from UTF-8 text/Markdown using only Python's stdlib.

No pip packages, internet, native programs, or installed system fonts are used.
The bundled TrueType font is embedded in full. Markdown tables, code, links,
and formula source remain readable text; this is not a LaTeX/HTML renderer.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import struct
import sys
import tempfile
import os
import zlib


class TrueType:
    """Read the Unicode cmap and horizontal metrics of a TrueType sfnt font."""

    def __init__(self, path):
        self.data = Path(path).read_bytes()
        if self.data[:4] not in (b'\x00\x01\x00\x00', b'true'):
            raise ValueError('The font must be a static TrueType .ttf with glyf outlines (not OTF/CFF, TTC, or WOFF).')
        count = self.u16(4)
        self.tables = {}
        for i in range(count):
            start = 12 + i * 16
            tag, _, offset, size = self.unpack('>4sIII', start)
            if offset + size > len(self.data):
                raise ValueError('The TrueType font contains an out-of-range table.')
            self.tables[tag] = (offset, size)
        for name in (b'head', b'hhea', b'hmtx', b'maxp', b'cmap', b'glyf'):
            if name not in self.tables:
                raise ValueError(f'The TrueType font is missing required table {name!r}.')
        if b'fvar' in self.tables:
            raise ValueError('Use the bundled static TrueType font; variable fonts are not supported by this fallback.')
        head = self.tables[b'head'][0]
        hhea = self.tables[b'hhea'][0]
        self.units = self.u16(head + 18)
        if not self.units:
            raise ValueError('Invalid TrueType unitsPerEm.')
        self.bbox = self.unpack('>hhhh', head + 36)
        self.ascent, self.descent = self.unpack('>hh', hhea + 4)
        self.glyph_count = self.u16(self.tables[b'maxp'][0] + 4)
        self.metric_count = self.u16(hhea + 34)
        if not 0 < self.metric_count <= self.glyph_count:
            raise ValueError('Invalid TrueType horizontal metrics.')
        metrics = self.tables[b'hmtx'][0]
        self.advances = [self.u16(metrics + i * 4) for i in range(self.metric_count)]
        self.cmap = self.read_cmap()
        self.ps_name = self.read_name()

    def unpack(self, fmt, offset):
        try:
            return struct.unpack_from(fmt, self.data, offset)
        except struct.error as exc:
            raise ValueError('The TrueType font is truncated or corrupt.') from exc

    def u16(self, offset):
        return self.unpack('>H', offset)[0]

    def read_name(self):
        if b'name' not in self.tables:
            return 'PaperChinese'
        base, size = self.tables[b'name']
        _, count, storage = self.unpack('>HHH', base)
        for i in range(count):
            platform, encoding, language, name_id, length, offset = self.unpack('>HHHHHH', base + 6 + i * 12)
            if name_id != 6 or platform not in (0, 3):
                continue
            raw = self.data[base + storage + offset:base + storage + offset + length]
            try:
                name = raw.decode('utf-16-be')
            except UnicodeError:
                continue
            name = re.sub(r'[^A-Za-z0-9_.-]', '', name)
            if name:
                return name
        return 'PaperChinese'

    def read_cmap(self):
        base, size = self.tables[b'cmap']
        end = base + size
        choices = []
        for i in range(self.u16(base + 2)):
            platform, encoding, relative = self.unpack('>HHI', base + 4 + i * 8)
            offset = base + relative
            if offset + 2 > end or not (platform == 0 or (platform == 3 and encoding in (1, 10))):
                continue
            fmt = self.u16(offset)
            if fmt in (4, 12):
                choices.append((fmt == 12, platform == 3, offset, fmt))
        if not choices:
            raise ValueError('The TrueType font has no supported Unicode cmap (format 4 or 12).')
        mapping = {}
        for _, _, offset, fmt in sorted(choices, reverse=True):
            local = self.cmap12(offset, end) if fmt == 12 else self.cmap4(offset, end)
            for cp, glyph in local.items():
                if 0 < glyph < self.glyph_count:
                    mapping.setdefault(cp, glyph)
        if not mapping:
            raise ValueError('The font has an empty Unicode cmap.')
        return mapping

    def cmap12(self, base, table_end):
        _, _, length, _, count = self.unpack('>HHIII', base)
        end = base + length
        if end > table_end or base + 16 + count * 12 > end:
            raise ValueError('Invalid cmap format 12 length.')
        result = {}
        previous = -1
        for i in range(count):
            start, stop, glyph = self.unpack('>III', base + 16 + i * 12)
            if start > stop or stop > 0x10FFFF or start <= previous:
                raise ValueError('Invalid cmap format 12 Unicode range.')
            for cp in range(start, stop + 1):
                result[cp] = glyph + cp - start
            previous = stop
        return result

    def cmap4(self, base, table_end):
        length, segments_twice = self.u16(base + 2), self.u16(base + 6)
        end = base + length
        segments = segments_twice // 2
        if end > table_end or base + 16 + segments * 8 > end:
            raise ValueError('Invalid cmap format 4 length.')
        stops = base + 14
        starts = stops + segments * 2 + 2
        deltas = starts + segments * 2
        offsets = deltas + segments * 2
        result = {}
        for i in range(segments):
            start, stop = self.u16(starts + i * 2), self.u16(stops + i * 2)
            delta = self.unpack('>h', deltas + i * 2)[0]
            ro = self.u16(offsets + i * 2)
            if start > stop:
                raise ValueError('Invalid cmap format 4 character range.')
            for cp in range(start, min(stop, 0xFFFE) + 1):
                if ro:
                    address = offsets + i * 2 + ro + (cp - start) * 2
                    if address + 2 > end:
                        raise ValueError('Invalid cmap format 4 glyph offset.')
                    raw = self.u16(address)
                    glyph = (raw + delta) & 0xFFFF if raw else 0
                else:
                    glyph = (cp + delta) & 0xFFFF
                if glyph:
                    result[cp] = glyph
        return result

    def width(self, char):
        glyph = self.cmap[ord(char)]
        return self.advances[min(glyph, self.metric_count - 1)] * 1000 / self.units

    def scale(self, value):
        return value * 1000 / self.units


def number(value):
    return f'{value:.4f}'.rstrip('0').rstrip('.') or '0'


class PDF:
    def __init__(self):
        self.objects = []

    def reserve(self):
        self.objects.append(None)
        return len(self.objects)

    def set(self, index, data):
        self.objects[index - 1] = data.encode('ascii') if isinstance(data, str) else data

    def add(self, data):
        index = self.reserve()
        self.set(index, data)
        return index

    def stream(self, data, extra=''):
        compressed = zlib.compress(data, 9)
        return self.add((f'<< /Length {len(compressed)} /Filter /FlateDecode {extra} >>\nstream\n').encode('ascii')
                        + compressed + b'\nendstream')

    def write(self, target, root, info):
        with open(target, 'wb') as out:
            out.write(b'%PDF-1.7\n%\xe2\xe3\xcf\xd3\n')
            offsets = [0]
            for index, obj in enumerate(self.objects, 1):
                if obj is None:
                    raise ValueError('An internal PDF object was not initialized.')
                offsets.append(out.tell())
                out.write(f'{index} 0 obj\n'.encode('ascii') + obj + b'\nendobj\n')
            xref = out.tell()
            out.write(f'xref\n0 {len(offsets)}\n0000000000 65535 f \n'.encode('ascii'))
            for offset in offsets[1:]:
                out.write(f'{offset:010d} 00000 n \n'.encode('ascii'))
            out.write((f'trailer\n<< /Size {len(offsets)} /Root {root} 0 R /Info {info} 0 R >>\n'
                       f'startxref\n{xref}\n%%EOF\n').encode('ascii'))


def make_pdf(text, font, output, title):
    # Expand tabs while retaining source line breaks and all visible Markdown text.
    text = text.replace('\r\n', '\n').replace('\r', '\n').expandtabs(4)
    controls = sorted({ord(ch) for ch in text if ord(ch) < 32 and ch != '\n'})
    if controls:
        raise ValueError('Input contains unsupported control characters: ' + ', '.join(f'U+{cp:04X}' for cp in controls))
    characters = sorted(set(text.replace('\n', '') + title + '第 页0123456789'), key=ord)
    missing = [ch for ch in characters if ord(ch) not in font.cmap]
    if missing:
        detail = ', '.join(f'U+{ord(ch):04X} {ch!r}' for ch in missing[:12])
        raise ValueError('Font lacks these characters: ' + detail + '. Replace decorative characters with plain text or use --font with a suitable static TrueType font.')
    if len(characters) > 65534:
        raise ValueError('Too many distinct characters for a single PDF CID font; split the document.')
    cids = {ch: i for i, ch in enumerate(characters, 1)}
    widths = {ch: font.width(ch) for ch in characters}

    def encoded(s):
        return b''.join(struct.pack('>H', cids[ch]) for ch in s).hex().upper()

    def measured(s, size):
        return sum(widths[ch] for ch in s) * size / 1000

    def wrap(line, size, max_width):
        # Break by glyph advance; this also wraps long URLs and code tokens safely.
        if not line:
            return ['']
        result, buf, total = [], [], 0.0
        for ch in line:
            advance = widths[ch] * size / 1000
            if buf and total + advance > max_width:
                result.append(''.join(buf))
                buf, total = [], 0.0
            buf.append(ch)
            total += advance
        if buf:
            result.append(''.join(buf))
        return result

    page_width, page_height = 595.276, 841.89
    margin, bottom, top = 46.0, 48.0, 44.0
    content_width = page_width - margin * 2
    pages, operations, cursor = [], [], page_height - top

    def new_page():
        nonlocal operations, cursor
        if operations:
            pages.append(operations)
        operations, cursor = [], page_height - top

    def line(s, size, color, leading):
        nonlocal cursor
        if cursor - leading < bottom:
            new_page()
        if s:
            operations.append(f'BT /F1 {number(size)} Tf {color} rg 1 0 0 1 {number(margin)} {number(cursor - size)} Tm <{encoded(s)}> Tj ET')
        cursor -= leading

    in_code = False
    for raw_line in text.split('\n'):
        fence = bool(re.match(r'^\s*(`{3,}|~{3,})', raw_line))
        heading = None if in_code or fence else re.match(r'^(#{1,6})\s+(.+)$', raw_line)
        if not raw_line:
            cursor -= 8
            continue
        if heading:
            level = len(heading.group(1))
            size = [20, 16, 13, 11.5, 11, 10.5][level - 1]
            parts = wrap(heading.group(2), size, content_width)
            leading = size * 1.45
            if cursor - leading * min(len(parts), 2) - 18 < bottom:
                new_page()
            elif operations:
                cursor -= 9
            for part in parts:
                line(part, size, '0.07 0.23 0.36', leading)
            cursor -= 4
        else:
            size = 8.7 if in_code or fence else (9.4 if raw_line.lstrip().startswith('|') else 10.5)
            leading = size * 1.6
            color = '0.21 0.27 0.32' if in_code or fence else '0.09 0.13 0.19'
            for part in wrap(raw_line, size, content_width):
                line(part, size, color, leading)
        if fence:
            in_code = not in_code
    if operations:
        pages.append(operations)
    if not pages:
        raise ValueError('The input did not contain any visible content.')

    pdf = PDF()
    catalog, pages_root = pdf.reserve(), pdf.reserve()
    font_file = pdf.stream(font.data, f'/Length1 {len(font.data)}')
    bbox = ' '.join(number(font.scale(n)) for n in font.bbox)
    descriptor = pdf.add(f'<< /Type /FontDescriptor /FontName /{font.ps_name} /Flags 32 /FontBBox [{bbox}] '
                         f'/ItalicAngle 0 /Ascent {number(font.scale(font.ascent))} /Descent {number(font.scale(font.descent))} '
                         f'/CapHeight {number(font.scale(font.ascent))} /StemV 80 /FontFile2 {font_file} 0 R >>')
    glyph_map = bytearray((len(characters) + 1) * 2)
    for ch, cid in cids.items():
        struct.pack_into('>H', glyph_map, cid * 2, font.cmap[ord(ch)])
    glyph_object = pdf.stream(bytes(glyph_map))
    font_widths = ' '.join(number(widths[ch]) for ch in characters)
    descendant = pdf.add(f'<< /Type /Font /Subtype /CIDFontType2 /BaseFont /{font.ps_name} '
                         f'/CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> '
                         f'/FontDescriptor {descriptor} 0 R /DW 1000 /W [1 [{font_widths}]] /CIDToGIDMap {glyph_object} 0 R >>')
    cmap = ['/CIDInit /ProcSet findresource begin', '12 dict begin', 'begincmap',
            '/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def',
            '/CMapName /PaperUnicode def', '/CMapType 2 def', '1 begincodespacerange', '<0000> <FFFF>', 'endcodespacerange']
    for offset in range(0, len(characters), 100):
        chunk = characters[offset:offset + 100]
        cmap.append(f'{len(chunk)} beginbfchar')
        cmap.extend(f'<{cids[ch]:04X}> <{ch.encode("utf-16-be").hex().upper()}>' for ch in chunk)
        cmap.append('endbfchar')
    cmap += ['endcmap', 'CMapName currentdict /CMap defineresource pop', 'end', 'end']
    unicode_map = pdf.stream('\n'.join(cmap).encode('ascii'))
    type0 = pdf.add(f'<< /Type /Font /Subtype /Type0 /BaseFont /{font.ps_name} /Encoding /Identity-H '
                   f'/DescendantFonts [{descendant} 0 R] /ToUnicode {unicode_map} 0 R >>')
    page_ids = []
    for index, ops in enumerate(pages, 1):
        footer = f'第 {index} 页'
        x = (page_width - measured(footer, 8)) / 2
        ops = ops + [f'0.82 0.86 0.89 RG 0.5 w {number(margin)} 34 m {number(page_width-margin)} 34 l S',
                     f'BT /F1 8 Tf 0.39 0.46 0.52 rg 1 0 0 1 {number(x)} 22 Tm <{encoded(footer)}> Tj ET']
        content = pdf.stream('\n'.join(ops).encode('ascii'))
        page_ids.append(pdf.add(f'<< /Type /Page /Parent {pages_root} 0 R /MediaBox [0 0 {number(page_width)} {number(page_height)}] '
                                f'/Resources << /Font << /F1 {type0} 0 R >> >> /Contents {content} 0 R >>'))
    pdf.set(pages_root, f'<< /Type /Pages /Count {len(page_ids)} /Kids [' + ' '.join(f'{p} 0 R' for p in page_ids) + '] >>')
    pdf.set(catalog, f'<< /Type /Catalog /Pages {pages_root} 0 R >>')
    info = pdf.add('<< /Title <FEFF' + title.encode('utf-16-be').hex().upper() + '> /Producer (Paper Logic Simplifier - Python stdlib) >>')
    pdf.write(output, catalog, info)
    return len(pages)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path, help='UTF-8 text or Markdown file')
    parser.add_argument('--output', required=True, type=Path, help='Destination .pdf file')
    parser.add_argument('--font', type=Path, help='Static Chinese .ttf (defaults to bundled font)')
    parser.add_argument('--title', help='PDF metadata title (defaults to input filename)')
    args = parser.parse_args()
    source = args.input.expanduser().resolve()
    output = args.output.expanduser().resolve()
    font_path = (args.font or Path(__file__).resolve().parent.parent / 'assets/fonts/NotoSansSC-Regular.ttf').expanduser().resolve()
    temporary = None
    try:
        if not source.is_file():
            raise FileNotFoundError(f'Input does not exist: {source}')
        if source == output:
            raise ValueError('--input and --output must be different files.')
        if output.suffix.lower() != '.pdf':
            raise ValueError('--output must have a .pdf extension.')
        if not font_path.is_file():
            raise FileNotFoundError(f'Font does not exist: {font_path}. Extract the complete export bundle or specify --font.')
        text = source.read_text(encoding='utf-8-sig')
        if not text.strip():
            raise ValueError('The input is empty. Write the complete summary before exporting.')
        font = TrueType(font_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix='.chatgpt-pdf-', suffix='.pdf', dir=output.parent, delete=False) as handle:
            temporary = Path(handle.name)
        pages = make_pdf(text, font, temporary, args.title or source.stem)
        if temporary.stat().st_size < 100 or not temporary.read_bytes().startswith(b'%PDF-'):
            raise ValueError('PDF output validation failed.')
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
