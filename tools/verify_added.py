"""Execute trusted authored Bash and Java outputs, never learner submissions.

Uses Bash in a fresh empty temporary directory and Java's compiler module when
javac is absent. Java 17 can audit the compatible subset; virtual-thread examples
need Java 21+. Other compilers are reported as unavailable, not counted as passes.
Run with uv run python tools/verify_added.py.
"""
import argparse
from pathlib import Path
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from codelingo.course import load_course
from codelingo.templates import render

BASH_SKIP = {'commands-read-4','redirection-read-1','redirection-read-2',
 'redirection-read-3','redirection-read-4','environment-read-3','robustness-read-2'}
JAVA_SKIP = {'toolchain-read-1','toolchain-read-2','toolchain-read-3','toolchain-read-4',
 'classes-read-4','errors-read-3','resources-read-3','records-read-4',
 'packages-read-1','packages-read-2','packages-read-3','packages-read-4',
 'testing-read-1'}


def audit_bash(seeds):
    count=0; failures=[]
    for seed in seeds:
        for template in load_course('bash').questions.values():
            if '-read-' not in template['id'] or template['id'] in BASH_SKIP:continue
            q=render(template,random.Random(seed))
            with tempfile.TemporaryDirectory(prefix='codelingo-bash-') as tmp:
                run=subprocess.run(['bash','--noprofile','--norc','-c',q['code']],cwd=tmp,
                    env={'PATH':os.environ['PATH'],'HOME':tmp,'LC_ALL':'C'},text=True,capture_output=True,timeout=5)
            expected='' if q['answer']=='(empty)' else q['answer']
            if run.returncode or run.stdout.strip()!=expected:
                failures.append((seed,q['id'],q['answer'],run.stdout.strip(),run.stderr))
            count+=1
    return count,failures


def audit_java(seeds):
    count=0; failures=[]
    java=shutil.which('java')
    if not java:return 0,[('Java unavailable',)]
    version=subprocess.run([java,'--version'],capture_output=True,text=True).stdout
    match=re.search(r'(?:openjdk|java) (\d+)',version)
    modern=bool(match and int(match[1])>=21)
    with tempfile.TemporaryDirectory(prefix='codelingo-java-') as tmp:
        cases=[]; error_cases=[]
        for seed in seeds:
            for template in load_course('java').questions.values():
                if '-read-' not in template['id'] or template['id'] in JAVA_SKIP:continue
                if template['id']=='threads-read-3' and not modern:continue
                q=render(template,random.Random(seed)); name='Case'+str(len(cases)+len(error_cases))
                code='public class '+name+' { public static void main(String[] args) throws Exception {\n'+q['code']+'\n}}'
                path=Path(tmp)/(name+'.java');path.write_text(code)
                case=(path,name,seed,q)
                (error_cases if q['answer'].startswith('Compile error') else cases).append(case)
        compiler=[java,'-m','jdk.compiler/com.sun.tools.javac.Main']
        run=subprocess.run(compiler+[str(c[0]) for c in cases],capture_output=True,text=True,timeout=60)
        if run.returncode:return 0,[('Java compile',run.stderr)]
        for path,name,seed,q in cases:
            run=subprocess.run([java,'-cp',tmp,name],capture_output=True,text=True,timeout=5)
            if run.returncode or run.stdout.strip()!=q['answer']:
                failures.append((seed,q['id'],q['answer'],run.stdout.strip(),run.stderr))
            count+=1
        for path,name,seed,q in error_cases:
            run=subprocess.run(compiler+[str(path)],capture_output=True,text=True,timeout=15)
            if not run.returncode:failures.append((seed,q['id'],'Expected rejection',run.stdout))
            count+=1
    return count,failures


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--language',choices=['all','bash','java'],default='all')
    args=parser.parse_args(); failures=[]
    for name,func in [('bash',audit_bash),('java',audit_java)]:
        if args.language not in ('all',name):continue
        count,errors=func((4,17));failures.extend(errors)
        print(f'{name}: {count} sampled programs, {len(errors)} failures')
        for error in errors:print(error)
    print('Scope: Bash and compatible Java output cards. Other languages, command descriptions, and modern Java features require their own toolchains/source review.')
    return bool(failures)

if __name__=='__main__':raise SystemExit(main())
