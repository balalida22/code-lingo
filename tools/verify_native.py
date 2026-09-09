"""Optional native prediction checks; requires gcc, g++, Perl, and Node.
Never runs learner submissions or intentionally undefined behavior.
"""
import sys,subprocess,tempfile,re,random,sqlite3,json,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from codelingo.course import load_course
from codelingo.templates import render
out=[];counts={}
with tempfile.TemporaryDirectory() as td:
 for cid in ('c','cpp','perl','web'):
  executable={'c':'gcc','cpp':'g++','perl':'perl','web':'node'}[cid]
  if not shutil.which(executable):
   counts[cid]='skipped: '+executable+' unavailable';continue
  count=0
  for q in load_course(cid).questions.values():
   if '-read-' not in q['id']:continue
   for seed in (4,17):
    x=render(q,random.Random(seed));code=x['code']; expected=x['answer']
    if x['prompt']!='What is the result?' or any(a in expected for a in ('error','Error','behavior','Throws','Panics','closed')):continue
    if cid=='web' and any(s in code for s in ('<script','document.','localStorage','// config.')):continue
    if cid=='perl' and x['id'].startswith('errors-read-2'):expected=expected.replace('\\n','\n')
    if cid in ('c','cpp'):
     pre=''; marker='/* in main */' if cid=='c' else '// in main'
     if marker in code:pre,code=code.split(marker,1)
     elif code.startswith('#define'):pre,code=code.split('\n',1)
     headers=('#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <limits.h>\n' if cid=='c' else '\n'.join('#include <'+h+'>' for h in ('iostream','string','vector','array','sstream','fstream','stdexcept','memory','optional'))+'\n')
     src=Path(td)/('test.c' if cid=='c' else 'test.cpp');src.write_text(headers+pre+'\nint main(void){\n'+code+'\n}\n')
     cmd=['gcc' if cid=='c' else 'g++','-std=c17' if cid=='c' else '-std=c++20',str(src),'-o',td+'/run']
     r=subprocess.run(cmd,capture_output=True,text=True)
     if r.returncode:out.append((cid,x['id'],seed,'COMPILE',r.stderr[:400]));continue
     cmd=[td+'/run']
    else:cmd=['perl','-e','use strict; use warnings; '+code] if cid=='perl' else ['node','-e',code]
    try:r=subprocess.run(cmd,capture_output=True,text=True,timeout=3)
    except subprocess.TimeoutExpired:out.append((cid,x['id'],'TIMEOUT'));continue
    if r.returncode or r.stdout.strip()!=expected.strip():out.append((cid,x['id'],seed,expected,r.stdout,r.stderr[:300]))
    count+=1
  counts[cid]=count
print(json.dumps({'counts':counts,'failures':out},indent=2))

if out: raise SystemExit(1)
