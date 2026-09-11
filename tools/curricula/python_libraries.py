"""Dedicated Python library tracks. Original Python sampler IDs stay intact."""
from build import emit, source

TRACKS={
 'numpy':('NumPy: arrays and numerical workflows','NumPy 2.x',[
  ('NumPy beginner guide','https://numpy.org/doc/stable/user/absolute_beginners.html'),
  ('NumPy broadcasting','https://numpy.org/doc/stable/user/basics.broadcasting.html'),
  ('NumPy copies and views','https://numpy.org/doc/stable/user/basics.copies.html')]),
 'matplotlib':('Matplotlib: figures and plotting workflows','Matplotlib 3.8+',[
  ('Matplotlib quick start','https://matplotlib.org/stable/users/explain/quick_start.html'),
  ('Figure and Axes API','https://matplotlib.org/stable/api/axes_api.html')]),
 'pytorch':('PyTorch: tensors, modules, and training code','PyTorch 2.x',[
  ('PyTorch beginner tutorials','https://docs.pytorch.org/tutorials/beginner/basics/intro.html'),
  ('Autograd mechanics','https://docs.pytorch.org/docs/stable/notes/autograd.html'),
  ('Serialization notes','https://docs.pytorch.org/docs/stable/notes/serialization.html')]),
 'transformers':('Transformers: tokenizers, models, and inference','Hugging Face Transformers 4.57 API baseline; PyTorch backend',[
  ('Transformers quick tour','https://huggingface.co/docs/transformers/v4.57.1/quicktour'),
  ('Padding and truncation','https://huggingface.co/docs/transformers/v4.57.1/pad_truncation'),
  ('Generation','https://huggingface.co/docs/transformers/v4.57.1/main_classes/text_generation'),
  ('Chat templates','https://huggingface.co/docs/transformers/v4.57.1/chat_templating')]),
}


def build():
 import importlib,json
 from build import DERIVED
 DERIVED.update(twom="m*2",mnext="m+1",add1="n+m+1",nminus2="n-2")
 from pathlib import Path
 for cid,(title,baseline,refs) in TRACKS.items():
  lessons=importlib.import_module('library_'+cid).lessons()
  for i,l in enumerate(lessons):
   l['section']='Basics' if i<4 else 'Intermediate' if i<8 else 'Advanced'
   for s in l['scenarios']:
    s['fragment']=s['fragment'].strip()
    if s.get('completion'):
     f=s['completion'];f['fragment']=f['fragment'].strip()
     f['goal']='Repair ____ to meet this contract: '+f['explanation']+' Target result: '+f['answer']+'.'
  emit(cid,'Python · '+title,baseline+'. Assumes Python functions, collections, and imports. Standard aliases: np=numpy, plt=matplotlib.pyplot, torch=PyTorch. Snippets are independent; stated model/tokenizer/file fixtures are assumed. The tutor never downloads models or executes learner code',
       [source(cid+'-'+str(i),label,url) for i,(label,url) in enumerate(refs)],lessons)
  # Library answers are Python fragments, so the existing safe AST matcher
  # permits equivalent spacing/quotes without running submissions.
  path=Path(__file__).resolve().parents[2]/'codelingo/courses'/f'{cid}.json'
  data=json.loads(path.read_text())
  for l in data['lessons']:
   for q in l['questions']:
    if q['kind']=='write':
     q['checker']='python_fragment'
     q['prompt']=q['prompt'].replace('preserving its spelling, spaces, and punctuation.','using equivalent Python syntax; spacing and quote style may vary.')
  path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
