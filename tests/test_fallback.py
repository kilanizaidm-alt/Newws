import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import refresh_classroom as f

class FallbackTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime.now(timezone.utc)
        self.row=dict(title='Test',url='https://news.un.org/en/story/test',publisher='UN News',language='en',published_at=self.now.isoformat(),text='PRIVATE ARTICLE TEXT')
    def test_feed_failure_retains_old_date(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(f.u,'DATA',Path(tmp)), patch.object(f.u,'read_feed',side_effect=ValueError()):
            path=Path(tmp)/'reports.json';path.write_text('{"fetched_at":"old"}')
            self.assertEqual(f.refresh_reports(self.now)[0],0)
            self.assertEqual(json.loads(path.read_text())['fetched_at'],'old')
    def test_reports_independent_no_article_republication(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(f.u,'DATA',Path(tmp)), patch.object(f.u,'read_feed',return_value=[self.row]):
            self.assertEqual(f.refresh_reports(self.now)[0],1)
            result=json.loads((Path(tmp)/'reports.json').read_text())
            self.assertNotIn('text',result['reports'][0])
    def test_ai_failure_still_publishes_links(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(f.u,'DATA',Path(tmp)), patch.object(f.u,'read_feed',return_value=[self.row]), patch.object(f,'enable_detailed_glossary'), patch.object(f.u,'main',side_effect=ValueError()):
            f.main()
            self.assertTrue((Path(tmp)/'reports.json').exists())
            self.assertEqual(json.loads((Path(tmp)/'refresh-status.json').read_text())['lesson_status'],'unavailable')
    def test_unmatched_glossary_example_rejected(self):
        import chunked_lesson as c
        story={k:'test' for k in c.u.FORMAT['stories'][0]}
        story.update(summary_en=' '.join(['word']*60),english_source_ids=['S1'],arabic_source_ids=[])
        term={k:'test' for k in c.u.FORMAT['glossary'][0]}
        with self.assertRaises(ValueError):
            c.story_check({'story':story,'glossary':[term]*4},{'id':'S1'},[])
    def test_rejected_story_stops_assembly(self):
        import chunked_lesson as c
        sources=[dict(id='S'+str(i),title='Test',language='en',published_at=self.now.isoformat(),text='Evidence') for i in range(5)]
        def fake(key,prompt,system=None):
            if prompt.startswith('Select five'):return {'ids':[s['id'] for s in sources]}
            if prompt.startswith('Review meaning'):return {'approved':False}
            return {'story':{},'glossary':[]}
        with patch.object(c.u,'generate',side_effect=fake), patch('openrouter_transport.verify_free_model',return_value=True):
            with self.assertRaises(ValueError):c.build('placeholder',sources,self.now)
    def test_paid_catalog_model_is_rejected(self):
        import openrouter_transport as t
        import io
        t.verify_free_model.cache_clear()
        model={'id':t.MODEL,'pricing':{'prompt':'0.001','completion':'0'},'reasoning':{'supported_efforts':['none']}}
        with patch.object(t.urllib.request,'build_opener') as opener:
            opener.return_value.open.return_value=io.BytesIO(json.dumps({'data':[model]}).encode())
            with self.assertRaises(ValueError):t.verify_free_model()
        t.verify_free_model.cache_clear()
    def test_wall_timeout_is_bounded(self):
        import openrouter_transport as t
        with patch.object(t,'verify_free_model',return_value=True), patch.object(t.subprocess,'run',side_effect=t.subprocess.TimeoutExpired('worker',180)):
            with self.assertRaisesRegex(ValueError,'request_wall_timeout'):
                t.generate('test-only','test','system')
    def test_completed_json_is_parsed(self):
        import openrouter_transport as t
        from types import SimpleNamespace
        result=SimpleNamespace(stdout=json.dumps({'finish':'stop','content':'{"ok": true}','completion_tokens':10}))
        with patch.object(t,'verify_free_model',return_value=True), patch.object(t.subprocess,'run',return_value=result):
            self.assertEqual(t.generate('test-only','test','system'),{'ok':True})
    def test_static_bank_has_eighteen_complete_entries(self):
        bank=json.loads((Path(__file__).resolve().parents[1]/'web/data/glossary-bank.json').read_text())
        self.assertEqual(len(bank['entries']),18)
        for row in bank['entries']:
            self.assertEqual(len(row),8)
            self.assertTrue(all(row.values()))

if __name__=='__main__': unittest.main()
