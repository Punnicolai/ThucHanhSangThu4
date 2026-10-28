"""Check staged snapshots, not unstaged working files. No secret values in logs."""
import importlib.metadata
import json
import os
from pathlib import Path
import re
import stat
import subprocess  # nosec B404
import sys
import tempfile
from datetime import datetime, timezone

PATTERNS = [r"(?i)\b(?:api[_-]?key|secret|password|token)\s*=\s*['\"][A-Za-z0-9_!@.-]{4,}['\"]", r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b', r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']


def git(*args):
    return subprocess.check_output(['git', *args])  # nosec B603 B607


def scan_sensitive(data):
    return any(re.search(pattern, data) for pattern in PATTERNS)


def check_permissions(mode, platform=os.name):
    return platform != 'nt' and bool(mode & stat.S_IWOTH)


def check_license(text, policy):
    findings=[]
    for line in text.splitlines():
        line=line.split('#',1)[0].strip()
        if not line: continue
        match=re.match(r'^([A-Za-z0-9_.-]+)==[^;\s]+(?:\s*;.*)?$',line)
        name=match.group(1).lower().replace('_','-') if match else None
        approved=policy['approved_packages'].get(name)
        if approved not in policy['allowed_licenses']:
            findings.append('Unapproved or unpinned dependency in requirements')
            continue
        try:
            metadata=importlib.metadata.metadata(name)
            expression=metadata.get('License-Expression')
            classifiers=metadata.get_all('Classifier') or []
            legacy=metadata.get('License','')
            valid=expression == approved or approved in legacy or any((approved=='BSD-3-Clause' and 'BSD License' in c) or (approved=='MIT' and 'MIT License' in c) or (approved=='Apache-2.0' and 'Apache Software License' in c) for c in classifiers)
            if not valid: findings.append(f'Installed license metadata differs from policy: {name}')
        except importlib.metadata.PackageNotFoundError:
            findings.append(f'Cannot verify dependency license; install requirements first: {name}')
    return findings


def main():
    root=Path(git('rev-parse','--show-toplevel').decode().strip())
    policy=json.loads((Path(__file__).parent/'license-policy.json').read_text(encoding='utf-8'))
    paths=git('diff','--cached','--name-only','--diff-filter=ACMR','-z').decode().split('\0')
    findings=[]
    with tempfile.TemporaryDirectory(prefix='gitsecure-') as folder:
        python_files=[]
        for index,name in enumerate(filter(None,paths)):
            payload=git('show',f':{name}')
            if len(payload)>2*1024*1024: findings.append(f'{name}: exceeds scanner size limit'); continue
            text=payload.decode('utf-8',errors='replace')
            if scan_sensitive(text): findings.append(f'{name}: possible hardcoded credential (value redacted)')
            target=root/name
            if target.exists() and check_permissions(target.stat().st_mode): findings.append(f'{name}: world-writable')
            if Path(name).name.startswith('requirements') and name.endswith('.txt'):
                findings.extend(f'{name}: {x}' for x in check_license(text,policy))
            if name.endswith('.py') or name.endswith('/pre-commit'):
                temp=Path(folder)/f'staged_{index}.py'; temp.write_bytes(payload); python_files.append(str(temp))
        if python_files:
            result=subprocess.run([sys.executable,'-m','bandit','-f','json','-q',*python_files],capture_output=True,text=True,check=False)  # nosec B603
            try:
                report=json.loads(result.stdout)
                findings.extend(f'Bandit {v["test_id"]} {v["issue_severity"]}: {Path(v["filename"]).name}:{v["line_number"]}' for v in report.get('results',[]))
                if report.get('errors') or result.returncode not in (0,1): findings.append('Bandit analysis error (fail closed)')
            except json.JSONDecodeError:
                findings.append('Bandit unavailable or returned invalid output (fail closed)')
    log=root/'gitsecure.log'
    with log.open('a',encoding='utf-8') as stream:
        stream.write(json.dumps({'timestamp':datetime.now(timezone.utc).isoformat(),'status':'blocked' if findings else 'passed','findings':findings})+'\n')
    print('COMMIT BLOCKED by GitSecure:' if findings else 'GitSecure: All checks passed.')
    for finding in findings: print(' -',finding)
    return 1 if findings else 0


if __name__=='__main__': sys.exit(main())
