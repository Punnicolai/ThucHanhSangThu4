import gzip
import json
import tempfile
import unittest
from pathlib import Path
from securelogger import get_secure_logger, verify_log, mask_pii

class LoggerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'secure.log'; self.key=b'k'*32
    def test_all_levels_json_and_masking(self):
        log=get_secure_logger(self.path,self.key)
        for level in (10,20,30,40,50):
            log.log(level,'User user@example.com\nFAKE ERROR',extra={'data':{'token':'demo-value','nested':{'email':'user@example.com','phone':'0901234567'}}})
        rows=[json.loads(x) for x in self.path.read_text(encoding='utf-8').splitlines()]
        self.assertEqual([r['level'] for r in rows],['DEBUG','INFO','WARNING','ERROR','CRITICAL'])
        self.assertNotIn('user@example.com',self.path.read_text(encoding='utf-8'))
        self.assertNotIn('demo-value',self.path.read_text(encoding='utf-8'))
        self.assertEqual(len(rows),5); self.assertTrue(verify_log(self.path,self.key))
    def test_tamper_detection(self):
        log=get_secure_logger(self.path,self.key); log.info('original')
        self.path.write_bytes(self.path.read_bytes().replace(b'original',b'modified'))
        self.assertFalse(verify_log(self.path,self.key))
        with self.assertRaises(ValueError): log.info('new event')
    def test_signature_tamper(self):
        log=get_secure_logger(self.path,self.key); log.info('event')
        Path(str(self.path)+'.sig').write_text('0'*64+'\n')
        self.assertFalse(verify_log(self.path,self.key))
    def test_missing_signature(self):
        self.path.write_text('{}\n'); self.assertFalse(verify_log(self.path,self.key))
    def test_rotate_and_verify_archives(self):
        log=get_secure_logger(self.path,self.key,max_bytes=220,backups=2)
        for i in range(8): log.info('event %d %s',i,'x'*60)
        archives=list(Path(self.temp.name).glob('*.gz'))
        self.assertEqual(len(archives),2)
        for archive in archives:
            self.assertTrue(verify_log(archive,self.key))
            with gzip.open(archive,'rt',encoding='utf-8') as f: json.loads(f.readline())
        self.assertTrue(verify_log(self.path,self.key))
    def test_recursive_redaction(self):
        self.assertEqual(mask_pii({'password':'x','list':['a@example.com']})['list'],['<email_masked>'])

if __name__=='__main__': unittest.main(verbosity=2)
