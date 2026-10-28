"""Run the actual logger API with synthetic input and verify real log files."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
base=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(base/'secure_logger_lab'))
from securelogger import verify_log
from securelogger.logger import get_key, get_secure_logger

def main():
    with tempfile.TemporaryDirectory(prefix='logger-demo-') as folder:
        os.environ['SECURE_LOG_PATH']=str(Path(folder)/'secure.log')
        spec=importlib.util.spec_from_file_location('logger_app',base/'secure_logger_lab/app.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        data={'email':'user@example.com','url':'https://8.8.8.8/','filename':'report.pdf','sql':"' OR 1=1 --",'html':'<script>alert(1)</script>','token':'SYNTHETIC-DEMO-ONLY'}
        response=module.app.test_client().post('/validate',json=data)
        path=Path(folder)/'secure.log';key=get_key(folder)
        content=path.read_text(encoding='utf-8')
        valid=verify_log(path,key)
        signatures=Path(str(path)+'.sig').read_text()
        path.write_bytes(path.read_bytes().replace(b'Validation performed',b'Validation modified'))
        tampered=verify_log(path,key)
        rotation=Path(folder)/'rotation.log'
        log=get_secure_logger(rotation,key,max_bytes=180,backups=2)
        for i in range(6): log.info('Rotation demo %d %s',i,'x'*60)
        archives=[{'name':f.name,'verified':verify_log(f,key)} for f in Path(folder).glob('rotation.log.*.gz')]
        if response.status_code!=200 or not valid or tampered or 'user@example.com' in content or 'SYNTHETIC-DEMO-ONLY' in content or len(archives)!=2 or not all(x['verified'] for x in archives): raise AssertionError('Demo failed')
        result={'request':data,'http_status':response.status_code,'response':response.get_json(),'masked_log':json.loads(content),'signature':signatures.strip(),'integrity_before_tamper':valid,'integrity_after_tamper':tampered,'compressed_archives':archives}
        dest=base/'docs/evidence';dest.mkdir(parents=True,exist_ok=True)
        (dest/'logger-demo.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
