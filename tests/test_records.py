import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from validate_record import validate_record, validate_exhibit, load_records, digest

ROOT=Path(__file__).resolve().parents[1]
BASE=json.loads((ROOT/'assets/record-template.json').read_text(encoding='utf-8'))
BASE.update(id='01', topic='工具测试论文', source='source.pdf', title='Synthetic test paper',
            journal='Test venue', reference='Synthetic fixture, not a real paper', doi='10.test/example')
BASE['article'].update(headline='测试标题', byline='测试元数据',
    figures=[{'page':1,'number':'Figure 1','box':[.1,.1,.9,.5],
              'caption':'测试图题','guide':'测试读图说明'}])
BASE['technical'].update(location='第 1 页', performance=[
    {'page':1,'number':'Table 1','box':[.1,.5,.9,.9], 'title':'测试结果表','guide':'测试表格说明'}])
BASE['narrative'].update(sections=[{'heading':'引言','paragraphs':['测试问题与方法'], 'figure_indices':[1]}],
    result_heading='测试实验',result_paragraphs=['测试结果'],closing='仅用于验证记录结构，不代表论文结论。')

class RecordValidation(unittest.TestCase):
    def test_new_paper_template(self):
        validate_record(BASE)
        template=json.loads((ROOT/'assets/record-template.json').read_text(encoding='utf-8'))
        with self.assertRaises(ValueError):validate_record(template)

    def test_narrative_references_and_summary(self):
        r=copy.deepcopy(BASE)
        for index in (2,3):
            r['article']['figures'].append(dict(r['article']['figures'][0],number=f'Figure {index}'))
            r['narrative']['sections'][0]['figure_indices'].append(index)
        validate_record(r)
        for indices in ([1,2], [1,2,2,3], [1,2,4], [True,2,3]):
            bad=copy.deepcopy(r);bad['narrative']['sections'][0]['figure_indices']=indices
            with self.assertRaises(ValueError):validate_record(bad)
        for value in ('', [], '第一段\n第二段'):
            bad=copy.deepcopy(r);bad['narrative']['closing']=value
            with self.assertRaises(ValueError):validate_record(bad)
        bad=copy.deepcopy(r);bad['narrative']['sections'][0]['paragraphs']=[]
        with self.assertRaises(ValueError):validate_record(bad)
        bad=copy.deepcopy(r);bad['technical']['performance'][0]['number']='Figure 1'
        with self.assertRaises(ValueError):validate_record(bad)

    def test_legacy_record_preserves_explicit_mode(self):
        r=copy.deepcopy(BASE);r['schema_version']=1;r.pop('narrative')
        r['article'].update(caption1='测试图题',guide1='测试读图说明')
        r['wechat']={'problem':'问题','method':'方法','result':'结果','conclusion':[
            {'title':f'历史要点 {i}','text':'历史正文'} for i in range(3)]}
        validate_record(r)
        r['schema_version']=2
        with self.assertRaises(ValueError):validate_record(r)

    def test_bad_crop_or_page(self):
        for box in ([.9,.1,.2,.9],[-.1,0,1,1],[0,0,1,2]):
            with self.assertRaises(ValueError):validate_exhibit({'page':1,'number':'图 1','box':box},'test',2)
        with self.assertRaises(ValueError):validate_exhibit({'page':3,'number':'图 1','box':[0,0,1,1]},'test',2)

    def test_source_identity_and_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'source.pdf').write_bytes(b'original')
            r=copy.deepcopy(BASE);r['source']='source.pdf';r['source_sha256']=digest(root/'source.pdf')
            validate_record(r,root)
            (root/'source.pdf').write_bytes(b'different edition')
            with self.assertRaises(ValueError):validate_record(r,root)
            r['source']='../outside.pdf'
            with self.assertRaises(ValueError):validate_record(r,root)

    def test_missing_evidence_must_be_explicit(self):
        r=copy.deepcopy(BASE);r['technical']['performance']=[]
        with self.assertRaises(ValueError):validate_record(r)
        r['technical']['performance_missing_reason']='原文为概念性方法说明，未提供定量实验。'
        r['article']['figures']=[]
        r['narrative']['sections'][0]['figure_indices']=[]
        with self.assertRaises(ValueError):validate_record(r)
        r['article']['route_missing_reason']='原文未给出流程或机制图。'
        validate_record(r)

    def test_duplicate_doi_and_unknown_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);r=copy.deepcopy(BASE)
            (root/'03.json').write_text(json.dumps(r))
            r['id']='99';r['source']='different.pdf';(root/'99.json').write_text(json.dumps(r))
            with self.assertRaises(ValueError):load_records(root)
            (root/'99.json').unlink()
            self.assertEqual(len(load_records(root, ids=['01'])),1)
            with self.assertRaises(ValueError):load_records(root,ids=['999'])

if __name__=='__main__':unittest.main()
