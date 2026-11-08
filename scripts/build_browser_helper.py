#!/usr/bin/env python3
"""Rebuild the offline PDF helper from vendored JS, font, and HTML template."""
from pathlib import Path
import base64

root = Path(__file__).resolve().parent.parent
page = (root / 'tools/pdf-export.template.html').read_text(encoding='utf-8')
for marker, file in [('/*__PDFMAKE__*/', 'tools/vendor/pdfmake.min.js'),
                     ('/*__MARKDOWNIT__*/', 'tools/vendor/markdown-it.min.js')]:
    assert page.count(marker) == 1, f'Expected exactly one {marker}'
    js = (root / file).read_text(encoding='utf-8').replace('</script', '<\\/script')
    page = page.replace(marker, js)
marker = '__CHINESE_FONT_BASE64__'
assert page.count(marker) == 1
page = page.replace(marker, base64.b64encode((root/'assets/fonts/NotoSansSC-Regular.ttf').read_bytes()).decode('ascii'))
licenses = '\n\n'.join((root / name).read_text(encoding='utf-8') for name in [
    'tools/vendor/pdfmake-LICENSE.txt', 'tools/vendor/markdown-it-LICENSE.txt', 'assets/fonts/OFL.txt'])
page = page.replace('</body>', '<script type="text/plain" id="third-party-licenses">\n' + licenses.replace('</script', '<\\/script') + '\n</script>\n</body>')
output = root / 'tools/pdf-export.html'
output.write_text(page, encoding='utf-8')
print(f'Offline browser helper built: {output} ({output.stat().st_size:,} bytes)')
