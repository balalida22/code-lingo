"""Audit authored NumPy/Matplotlib examples without executing learner input.
Run with a Python interpreter containing numpy and matplotlib, independently of
Code Lingo's dependency-free uv environment. Uses Agg and temporary files.
"""
import contextlib
import io
import os
from pathlib import Path
import random
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from codelingo.course import load_course
from codelingo.templates import render


def main():
 import numpy as np
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 print('Native versions:',np.__version__,matplotlib.__version__)
 failures=[]; count=0
 for cid in ('numpy','matplotlib'):
  for seed in (4,17,29):
   for template in load_course(cid).questions.values():
    if '-read-' not in template['id'] and '-write-repair-' not in template['id']:continue
    q=render(template,random.Random(seed)); code=q['code']
    expected=q.get('answer',q.get('target_answer'))
    if q['kind']=='write':code=code.replace('____',q['accepted'][0])
    out=io.StringIO();error=None
    previous=os.getcwd()
    with tempfile.TemporaryDirectory(prefix='codelingo-lib-') as tmp:
     try:
      os.chdir(tmp)
      with contextlib.redirect_stdout(out):
       exec(compile(code,'<authored '+q['id']+'>','exec'),{'np':np,'plt':plt})
     except Exception as exc:error=exc
     finally:
      os.chdir(previous);plt.close('all')
    ok=isinstance(error,ValueError) if expected.startswith('ValueError:') else error is None and out.getvalue().strip()==expected
    if not ok:failures.append((cid,seed,q['id'],expected,out.getvalue().strip(),repr(error)))
    count+=1
 print(count,'authored output/repair variants;',len(failures),'failures')
 for f in failures:print(f)
 print('PyTorch and Transformers were not executed by this audit.')
 return bool(failures)

if __name__=='__main__':raise SystemExit(main())
