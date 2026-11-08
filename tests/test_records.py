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
    figures=[{'page':1,'number':'Figure 1','box':[.1,.1,.9,.5]}],
    caption1='测试图题', guide1='测试读图说明')
BASE['technical'].update(location='第 1 页', performance=[
    {'page':1,'number':'Table 1','box':[.1,.5,.9,.9], 'title':'测试结果表','guide':'测试表格说明'}])
BASE['wechat'].update(problem='测试问题',method='测试方法',result='测试结果')
for i, section in enumerate(BASE['wechat']['conclusion'], 1):
    section['title']=f'测试做法 {i}'
    section['text']='仅用于验证记录结构，不代表论文结论。'

class RecordValidation(unittest.TestCase):
    def test_new_paper_template(self):
        validate_record(BASE)
        template=json.loads((ROOT/'assets/record-template.json').read_text(encoding='utf-8'))
        with self.assertRaises(ValueError):validate_record(template)

    def test_takeaway_count_and_substance(self):
        for count in (3,4,5):
            r=copy.deepcopy(BASE)
            r['wechat']['conclusion']=[copy.deepcopy(BASE['wechat']['conclusion'][0]) for _ in range(count)]
            validate_record(r)
        for count in (0,2,6):
            r=copy.deepcopy(BASE)
            r['wechat']['conclusion']=[copy.deepcopy(BASE['wechat']['conclusion'][0]) for _ in range(count)]
            with self.assertRaises(ValueError):validate_record(r)
        r=copy.deepcopy(BASE);r['wechat']['conclusion'][0]['title']=''
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
