"""Use a disposable repository; never stage bad.py in the user's real repo."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

base=Path(__file__).resolve().parents[1]
def main():
    with tempfile.TemporaryDirectory(prefix='gitsecure-demo-') as folder:
        root=Path(folder)
        shutil.copytree(base/'gitsecure',root/'gitsecure',ignore=shutil.ignore_patterns('__pycache__','tests'))
        shutil.copytree(base/'.githooks',root/'.githooks')
        hook=root/'.githooks/pre-commit'
        if os.name == 'nt':
            lines=hook.read_text(encoding='utf-8').splitlines()
            lines[0]='#!'+Path(sys.executable).as_posix()
            hook.write_text('\n'.join(lines)+'\n',encoding='utf-8')
        hook.chmod(0o755)
        def run(*args):
            result=subprocess.run(['git',*args],cwd=root,capture_output=True,text=True,check=False)
            return {'code':result.returncode,'output':result.stdout+result.stderr}
        for args in [('init',),('config','user.name','Lab Demo'),('config','user.email','demo@example.com'),('config','core.hooksPath','.githooks')]:
            result=run(*args)
            if result['code']: raise RuntimeError(result['output'])
        bad=root/'bad.py'
        bad.write_text('password = '+repr('FAKE'+'123456789')+'\n',encoding='utf-8')
        run('add','bad.py'); blocked=run('commit','-m','demo should be blocked')
        if blocked['code']==0 or 'COMMIT BLOCKED by GitSecure' not in blocked['output']:
            raise RuntimeError('Hook did not run as expected: '+blocked['output'])
        bad.write_text('import os\ncredential = os.environ.get("DEMO_CREDENTIAL")\n',encoding='utf-8')
        run('add','bad.py'); passed=run('commit','-m','demo safe code')
        if passed['code']: raise RuntimeError(passed['output'])
        result={'blocked_commit':blocked,'safe_commit':passed,'log':json.loads((root/'gitsecure.log').read_text().splitlines()[0])}
        dest=base/'docs/evidence';dest.mkdir(parents=True,exist_ok=True)
        (dest/'hook-demo.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
