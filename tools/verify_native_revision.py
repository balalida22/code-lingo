"""Execute trusted, authored output predictions and repaired programs.

Never executes user submissions, undefined behavior, external commands from
cards, network requests, or browser-dependent snippets. Reports skipped scopes.
Compiler diagnostics and conceptual cards receive separate editorial review.
Run: uv run python tools/verify_native_revision.py
"""
import argparse
import ctypes.util
import json
from pathlib import Path
import random
import shutil
import sqlite3
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from codelingo.course import load_course
from codelingo.templates import render

C_HEADERS=('stdio.h','stdlib.h','string.h','limits.h','stdint.h','assert.h')
CPP_HEADERS=('iostream','string','vector','array','sstream','fstream','stdexcept',
 'memory','optional','span','variant','concepts','thread','atomic','mutex','cassert')

def sql_output(code,params):
    with sqlite3.connect(':memory:',isolation_level=None) as db:
        statement='';cursor=None
        for char in code:
            statement+=char
            if char==';' and sqlite3.complete_statement(statement):
                cursor=db.execute(statement,{'size':params.get('n',3)})
                statement=''
        if statement.strip():cursor=db.execute(statement)
        return '; '.join(', '.join('NULL' if v is None else str(v) for v in row) for row in cursor.fetchall())

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--courses',nargs='+',default=['c','cpp','lua','perl','ruby','php','typescript','web','sql'])
    parser.add_argument('--seeds',nargs='+',type=int,default=[4,17])
    args=parser.parse_args();failures=[];counts={};skipped={}
    with tempfile.TemporaryDirectory(prefix='codelingo-authored-') as temp:
        td=Path(temp)
        for cid in args.courses:
            executable={'c':'gcc','cpp':'g++','lua':'lua5.4','perl':'perl','ruby':'ruby','php':'php','typescript':'tsc','web':'node','sql':None}[cid]
            lua_library=cid=='lua' and ctypes.util.find_library('lua5.4')
            if executable and not shutil.which(executable) and not lua_library:
                skipped[cid]=executable+' unavailable';continue
            if cid=='typescript':
                run=subprocess.run([sys.executable,str(ROOT/'tools/verify_typescript.py')],capture_output=True,text=True,timeout=180)
                try:
                    report=json.loads(run.stdout)
                    counts[cid]=report['output_programs']
                    counts['typescript_expected_type_failures']=report['expected_type_failures']
                    failures.extend(dict(course=cid,**item) for item in report['failures'])
                    if run.returncode and not report['failures']:failures.append({'course':cid,'error':run.stderr or run.stdout})
                except (ValueError,KeyError):failures.append({'course':cid,'error':run.stdout+run.stderr})
                continue
            counts[cid]=0;omitted=0
            for template in load_course(cid).questions.values():
                repaired=template.get('target_answer') is not None
                if not repaired and ('-read-' not in template['id'] or template['prompt']!='What is the result?'):
                    omitted+=1;continue
                for seed in args.seeds:
                    q=render(template,random.Random(seed));code=q['code']
                    expected=q['target_answer'] if repaired else q['answer']
                    if repaired:code=code.replace('____',q['accepted'][0])
                    if any(token in expected.lower() for token in ('error','undefined behavior','throws','raises','panics','compile','closed')):
                        omitted+=1;continue
                    if cid=='web' and any(token in code for token in ('<script','document.','localStorage','fetch(','// config.','list.','form.')):
                        omitted+=1;continue
                    try:
                        if cid=='sql':
                            actual=sql_output(code,q.get('variant',{}))
                        else:
                            if cid in ('c','cpp'):
                                pre='';marker='/* in main */' if cid=='c' else '// in main'
                                if marker in code:pre,code=code.split(marker,1)
                                elif code.startswith('#define'):pre,code=code.split('\n',1)
                                headers=C_HEADERS if cid=='c' else CPP_HEADERS
                                src=td/('fixture.c' if cid=='c' else 'fixture.cpp')
                                src.write_text(''.join('#include <'+h+'>\n' for h in headers)+pre+'\nint main(void){\n'+code+'\n}\n')
                                run=subprocess.run([executable,'-std=c17' if cid=='c' else '-std=c++20','-pthread',str(src),'-o',str(td/'run')],capture_output=True,text=True,timeout=20)
                                if run.returncode:raise RuntimeError(run.stderr[:900])
                                cmd=[str(td/'run')]
                            else:
                                src=td/'fixture.txt'
                                src.write_text(('<?php\n' if cid=='php' else 'use strict; use warnings;\n' if cid=='perl' else '')+code)
                                cmd=([sys.executable,str(ROOT/'tools/verify_lua.py'),str(src)] if lua_library else [executable,str(src)])
                            run=subprocess.run(cmd,cwd=td,capture_output=True,text=True,timeout=5)
                            if run.returncode:raise RuntimeError(run.stderr[:900])
                            actual=run.stdout.strip()
                        if cid=='perl' and q['id']=='errors-read-2':expected=expected.replace('\\n','\n')
                        if actual.strip()!=expected.strip():raise AssertionError(f'expected {expected!r}; got {actual!r}')
                        counts[cid]+=1
                    except Exception as error:
                        failures.append({'course':cid,'question':q['id'],'seed':seed,'error':str(error)})
            skipped[cid+'_cards']=omitted
    print(json.dumps({'verified_programs':counts,'skipped':skipped,'failures':failures},indent=2))
    return int(bool(failures))

if __name__=='__main__':raise SystemExit(main())
