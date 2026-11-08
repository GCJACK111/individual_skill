"""Check generated content, pages and image count; render all pages for human visual QA."""
from contextlib import closing
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import pypdfium2 as pdfium
from validate_record import load_records


def normalize(text):
    return ''.join(text.split())


def inspect_one(path, record):
    with pdfium.PdfDocument(path) as doc:
        texts, images, sizes = [], 0, []
        for i in range(len(doc)):
            with closing(doc[i]) as page:
                with closing(page.get_textpage()) as tp:
                    text = normalize(tp.get_text_bounded())
                if f'{i+1}/{len(doc)}' not in text:
                    raise ValueError(f'{path.name} page {i+1}: missing/wrong footer')
                if abs(page.get_width()-500) > .01 or page.get_height() > 1440:
                    raise ValueError(f'{path.name}: unexpected page dimensions')
                images += len(list(page.get_objects(filter=[pdfium.raw.FPDF_PAGEOBJ_IMAGE])))
                sizes.append(list(page.get_size())); texts.append(text)
        full = ''.join(texts)
        required = [record['article']['headline'], record['title']]
        figures = record['article']['figures']; perf = record['technical'].get('performance', [])
        if record.get('schema_version', 1) == 2:
            narrative = record['narrative']
            if normalize(narrative['closing']) not in texts[-1]:
                raise ValueError(f'{path.name}: missing complete closing paragraph')
            ordered = []
            for section in narrative['sections']:
                required.append(section['heading'])
                required.extend(section['paragraphs'])
                ordered.extend([section['heading'], *section['paragraphs']])
                for index in section.get('figure_indices', []):
                    f = figures[index-1]
                    label = f"原文{f['number']} · PDF 第 {f['page']} 页"
                    required.extend([f['caption'], f['guide'], label])
                    ordered.extend([label, f['guide']])
            required.extend([narrative['result_heading'], *narrative['result_paragraphs'], narrative['closing']])
            ordered.extend([narrative['result_heading'], *narrative['result_paragraphs']])
            for e in perf:
                ordered.extend([e['title'], *e.get('paragraphs', []), f"原文{e['number']} · PDF 第 {e['page']} 页", e['guide']])
            ordered.append(narrative['closing'])
            cursor = 0
            for value in ordered:
                found = full.find(normalize(value), cursor)
                if found < 0:
                    raise ValueError(f'{path.name}: missing or out-of-order article content {value[:60]}')
                cursor = found + len(normalize(value))
            expected_images = len(figures) + len(perf)
        else:
            required += [record['wechat'][key] for key in ('problem','method','result')]
            for item in record['wechat']['conclusion']:
                for key in ('title','text'):
                    if normalize(item[key]) not in texts[-1]:
                        raise ValueError(f'{path.name}: missing conclusion {key}')
            dedup = len(figures) > 1 and any((e['page'],e['number']) == (figures[1]['page'],figures[1]['number']) for e in perf)
            expected_images = min(2,len(figures)) - int(dedup) + len(perf)
            for i, fig in enumerate(figures[:2], 1):
                if i == 2 and dedup:
                    continue
                required += [record['article'][f'caption{i}'],record['article'][f'guide{i}']]
        if images != expected_images:
            raise ValueError(f'{path.name}: {images} images, expected {expected_images}')
        for e in perf:
            required += [e['title'],e['guide'],f"原文{e['number']} · PDF 第 {e['page']} 页"]
        for value in required:
            if normalize(value) not in full:
                raise ValueError(f'{path.name}: missing expected text {value[:60]}')
        return {'id':record['id'],'pages':len(doc),'images':images,'performance_exhibits':len(perf),'page_sizes':sizes}


def render_worker(pdf, out):
    out.mkdir(parents=True, exist_ok=True)
    # Run once per document so native renderer/font state cannot leak across PDFs.
    with pdfium.PdfDocument(pdf) as doc:
        for i in range(len(doc)):
            with closing(doc[i]) as page:
                bitmap=page.render(scale=1.5)
                try:bitmap.to_pil().convert('RGB').save(out/f'page-{i+1:03}.png')
                finally:bitmap.close()


def main():
    if len(sys.argv)>1 and sys.argv[1]=='_render':
        render_worker(Path(sys.argv[2]),Path(sys.argv[3])); return
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--records', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--qa', required=True, type=Path)
    p.add_argument('--ids', nargs='+')
    p.add_argument('--renderer', choices=['auto','poppler','pdfium'], default='auto')
    args=p.parse_args(); records=load_records(args.records,ids=args.ids)
    poppler=os.environ.get('PDFTOPPM') or shutil.which('pdftoppm')
    if args.renderer=='poppler' and not poppler:
        p.error('pdftoppm missing; install Poppler or select --renderer pdfium')
    args.qa.mkdir(parents=True,exist_ok=True); results=[]
    for record in records:
        path=args.output/f"{record['id']} {record['topic']}.pdf"
        results.append(inspect_one(path, record))
        out=args.qa/record['id'];out.mkdir(parents=True,exist_ok=True)
        if poppler and args.renderer!='pdfium':
            subprocess.run([poppler,'-r','108','-png',str(path),str(out/'page')],check=True,capture_output=True)
        else:
            subprocess.run([sys.executable,__file__,'_render',str(path),str(out)],check=True)
    report={'status':'structural_checks_passed_visual_review_required','papers':len(results),'pages':sum(x['pages'] for x in results),'performance_exhibits':sum(x['performance_exhibits'] for x in results),'details':results}
    (args.qa/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='details'},ensure_ascii=False))
    print('Open rendered PNGs; text/image counts do not verify crops, values or visual legibility.')


if __name__=='__main__':
    main()
