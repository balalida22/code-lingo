"""Optional batched TypeScript checks for authored fixtures, including errors.

Requires tsc >=4.9 and Node. Does not run shell/configuration teaching cards or
learner submissions. Emits fixtures into a temporary directory, checks expected
type failures, and executes successfully checked output/repair cases.
"""
import argparse
import json
from pathlib import Path
import random
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from codelingo.course import load_course
from codelingo.templates import render

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tsc',default='tsc')
    args=parser.parse_args()
    if not shutil.which(args.tsc) or not shutil.which('node'):
        print('Install tsc and Node or pass --tsc /path/to/tsc');return 2
    groups={};failures=[];passed=0;rejected=0
    with tempfile.TemporaryDirectory(prefix='codelingo-ts-') as temp:
        root=Path(temp)
        for template in load_course('typescript').questions.values():
            repair=template.get('target_answer') is not None
            type_error=template.get('answer','').startswith('Type error')
            if not repair and not ('-read-' in template['id'] and (type_error or template['prompt']=='What is the result?')):continue
            for seed in (4,17):
                q=render(template,random.Random(seed));code=q['code']
                if repair:code=code.replace('____',q['accepted'][0])
                folder=root/(q['id']+'-'+str(seed));folder.mkdir()
                config=None
                if '// app.ts\n' in code:
                    config,code=code.split('// app.ts\n',1)
                    config=config.removeprefix('// config.ts\n')
                elif code.startswith('// config.ts exports '):
                    config,code=code.split('\n',1)
                    config=config.removeprefix('// config.ts exports ')+';'
                    config='export '+config
                if config is not None:(folder/'config.ts').write_text(config)
                (folder/'app.ts').write_text('export {};\n'+code)
                flags=tuple(flag for flag in ('exactOptionalPropertyTypes','noUncheckedIndexedAccess') if flag in code)
                groups.setdefault(flags,[]).append((folder,q['id'],seed,type_error,q.get('target_answer',q.get('answer'))))
        for flags,cases in groups.items():
            cmd=[args.tsc,'--strict','--target','ES2022','--module','commonjs','--pretty','false']
            cmd+=['--'+flag for flag in flags]
            cmd+=[str(folder/'app.ts') for folder,*_ in cases]
            run=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
            diagnostics={}
            for line in run.stdout.splitlines():
                match=re.match(r'(.+\.ts)\(\d+,\d+\): error TS\d+: (.*)',line)
                if match:
                    diagnostics.setdefault(Path(match[1]).resolve().parent,[]).append(match[2])
                elif line and not line.startswith(' '):failures.append({'compiler':line})
            if run.stderr:failures.append({'compiler_stderr':run.stderr})
            if run.returncode and not diagnostics:failures.append({'compiler_returncode':run.returncode})
            for folder,qid,seed,type_error,expected in cases:
                errors=diagnostics.get(folder,[])
                if bool(errors)!=type_error:
                    failures.append({'question':qid,'seed':seed,'expected_type_error':type_error,'diagnostics':errors});continue
                if type_error:rejected+=1;continue
                run=subprocess.run(['node',str(folder/'app.js')],capture_output=True,text=True,timeout=5)
                if run.returncode or run.stdout.strip()!=expected.strip():
                    failures.append({'question':qid,'seed':seed,'expected':expected,'output':run.stdout,'stderr':run.stderr})
                else:passed+=1
    print(json.dumps({'output_programs':passed,'expected_type_failures':rejected,'failures':failures},indent=2))
    return int(bool(failures))

if __name__=='__main__':raise SystemExit(main())
