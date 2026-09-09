"""Optional native audit of Rust predictions and repairs. Requires rustc 1.90+.
Compiles only authored course snippets, never learner input; no network/crates.
Command/file-tree questions and execution-model explanations use source review.
"""
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

ERROR_CODES={
 'bindings-read-3':'E0384','ownership-read-1':'E0382','ownership-read-4':'E0382',
 'borrowing-read-3':'E0515','collections-read-map-ownership':'E0382',
 'lifetimes-read-4':'E0597','threads-read-4':'E0277',
 'trait-objects-read-4':'E0038','advanced-rust-read-2':'E0384',
}


def prepare(q):
    """Return source, compiler mode, expected output, arguments, error code."""
    qid=q['id'];code=q['code'];mode='run';args=[]
    if '-read-' in qid:expected=q['answer']
    elif '-write-repair-' in qid:
        code=code.replace('____',q['accepted'][0])
        expected=re.search(r'Target result: (.*)\. Enter only',q['prompt'],re.S).group(1)
    else:return None
    if qid.startswith(('cargo-','workspaces-')) or qid=='testing-read-3':return None
    if qid in ERROR_CODES:mode='compile_error'
    elif expected.startswith('Panics:'):mode='panic'
    elif qid.startswith('testing-'):mode='test'
    elif qid=='async-read-2':
        code+='\nlet waker=std::task::Waker::noop(); let mut cx=std::task::Context::from_waker(waker); let mut task=std::pin::pin!(run()); match std::future::Future::poll(task.as_mut(),&mut cx) {std::task::Poll::Ready(value)=>println!("{value}"),std::task::Poll::Pending=>panic!("expected immediate completion")}'
    elif qid in ('async-read-3','async-read-4','trait-objects-write-repair-4'):mode='compile'
    elif qid=='io-read-arguments':args=[q['variant']['word']]
    elif qid=='io-read-file-errors':code+='\nassert!(load("absent-audit-file.txt").is_err());';expected=''
    elif qid=='io-read-stderr':mode='stderr';expected='invalid size: '+str(q['variant']['n'])
    elif qid=='io-read-exit-status':mode='failure_exit';expected='missing path'
    if not re.search(r'\bfn main\s*\(',code) and mode!='test':code='fn main(){\n'+code+'\n}'
    return code,mode,expected,args,ERROR_CODES.get(qid)


def main():
    compiler=shutil.which('rustc')
    if not compiler:
        print('Rust audit not run: install Rust 1.90+ with edition 2024 support, then rerun this command.',file=sys.stderr)
        return 2
    failures=[];counts={};skipped=set()
    with tempfile.TemporaryDirectory(prefix='codelingo-rust-') as tmp:
        for seed in (4,17):
            for family in load_course('rust').questions.values():
                if '-read-' not in family['id'] and '-write-repair-' not in family['id']:continue
                q=render(family,random.Random(seed));case=prepare(q)
                if case is None:skipped.add(q['id']);continue
                code,mode,expected,args,error_code=case
                src=Path(tmp)/'question.rs';binary=Path(tmp)/'question'
                src.write_text(code)
                command=[compiler,'--edition=2024','--error-format=json','-o',str(binary),str(src)]
                if mode=='test':command.insert(1,'--test')
                compiled=subprocess.run(command,capture_output=True,text=True,timeout=30)
                issue=None
                if mode=='compile_error':
                    if compiled.returncode==0 or error_code not in compiled.stderr:issue='Expected compiler diagnostic '+str(error_code)
                elif compiled.returncode:issue='Unexpected compilation failure: '+compiled.stderr[-1500:]
                elif mode!='compile':
                    result=subprocess.run([str(binary),*args],cwd=tmp,capture_output=True,text=True,timeout=5)
                    if mode=='test':
                        if result.returncode:issue='Test harness failed: '+result.stdout+result.stderr
                    elif mode=='panic':
                        if result.returncode==0 or 'borrow' not in result.stderr.lower():issue='Expected RefCell borrow panic'
                    elif mode=='failure_exit':
                        if result.returncode==0 or result.stderr.strip()!=expected:issue='Incorrect failure exit or stderr'
                    elif mode=='stderr':
                        if result.returncode or result.stdout or result.stderr.strip()!=expected:issue='Incorrect stderr output'
                    elif result.returncode or result.stdout.strip()!=expected.strip():issue=f'Expected {expected!r}, got {result.stdout!r}; stderr: {result.stderr}'
                counts[mode]=counts.get(mode,0)+1
                if issue:failures.append({'id':q['id'],'seed':seed,'issue':issue})
    print(json.dumps({'checks':counts,'reference_review_only':sorted(skipped),'failures':failures},indent=2))
    return bool(failures)

if __name__=='__main__':raise SystemExit(main())
