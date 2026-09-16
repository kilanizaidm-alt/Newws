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
    def test_static_bank_has_eighteen_complete_entries(self):
        bank=json.loads((Path(__file__).resolve().parents[1]/'web/data/glossary-bank.json').read_text())
        self.assertEqual(len(bank['entries']),18)
        for row in bank['entries']:
            self.assertEqual(len(row),8)
            self.assertTrue(all(row.values()))

if __name__=='__main__': unittest.main()
