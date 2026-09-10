"""Rebuild authored CLQ courses. Run: uv run python tools/curricula/build.py.
Each scenario produces prediction + code-completion MCQs and a writing card.
These are scaffolded stages of one concept, with independently sampled literals.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARAMS = {'n': {'type':'int','min':3,'max':19}, 'm': {'type':'int','min':2,'max':7},
          'word': {'type':'choice','values':['cache','buffer','panel','message','record']}}
DERIVED = {'add':'n+m','mul':'n*m','next':'n+1','prev':'n-1','double':'n*2',
           'rem':'n%m','div':'n//m','length':'len(word)','first':'word[0]',
           'upper':'upper(word)','joined':'word+word','square':'n*n','plus2':'n+2'}

def S(code, answer, wrong, explanation, bad, prompt='What is the result?'):
    """Mark exactly one fragment with ~ delimiters; bad gives distractor fragments."""
    parts=code.split('~')
    assert len(parts)==3, code
    return dict(code=(parts[0]+parts[1]+parts[2]).replace('__TILDE__','~'), blank=(parts[0]+'____'+parts[2]).replace('__TILDE__','~'),
                fragment=parts[1].replace('__TILDE__','~'), answer=str(answer), wrong=[x or '(empty)' for x in wrong.replace('|||','|__OR__|').strip('|').split('|')],
                explanation=explanation, bad=[x.replace('__OR__','||') or '(empty)' for x in bad.replace('|||','|__OR__|').strip('|').split('|')], prompt=prompt)

def lesson(lid, title, notes, *scenarios):
    assert scenarios, (lid, "At least one scenario is required")
    return dict(id=lid,title=title,notes=notes,scenarios=scenarios)

def emit(cid,title,baseline,sources,lessons,version='1.0'):
    if cid not in ('rust','python'):
        from native_revision import upgrade
        sources,lessons=upgrade(cid,sources,lessons)
        version='1.1'
    assert lessons, cid
    data=dict(schema_version=2,id=cid,title=title,language=baseline,version=version,sources=sources,lessons=[])
    for index,l in enumerate(lessons):
        qs=[];writes=[]
        for j,s in enumerate(l['scenarios'],1):
            base=dict(concept=l['title'], explanation=s['explanation'], hint=s.get('hint',s['explanation']),parameters=PARAMS,derived=DERIVED)
            stem=s.get('id',str(j))
            q=dict(base,id=f"{l['id']}-read-{stem}",kind='mcq',code=s['code'],prompt=s['prompt'],answer=s['answer'],options=[s['answer']]+s['wrong'])
            qs.append(q)
            if s.get('completion'):
                if cid!='rust':
                    q['repair_question_id']=f"{l['id']}-write-repair-{stem}"
                s=s['completion']
                stem='repair-'+stem
                base=dict(base,explanation=s['explanation'],hint=s.get('hint',s['explanation']))
            goal='Complete ____ using the demonstrated construction. Target result: '+s['answer']+'. '+s['explanation']
            if re.fullmatch(r"(?:\$\{(?:n|m|word)\}|'[^']*'|\"[^\"]*\")", s['fragment']):
                goal+=' Use '+s['fragment']+' as the replacement literal.'
            goal=s.get('goal',goal)
            qs.append(dict(base,id=f"{l['id']}-choose-{stem}",kind='mcq',code=s['blank'],prompt=goal,answer=s['fragment'],options=[s['fragment']]+s['bad']))
            card=dict(base,id=f"{l['id']}-write-{stem}",kind='write',checker='exact',code=s['blank'],prompt=goal+' Enter only the missing fragment, preserving its spelling, spaces, and punctuation.',accepted=[s['fragment']])
            if cid in ('c','cpp') and not s['code'].lstrip().startswith('$') and '#' not in s['fragment']:
                card['checker']='c_tokens'
                card['prompt']=goal+' Enter only the missing fragment. Whitespace between C/C++ tokens may vary; preserve spelling, literals, and punctuation.'
            if cid not in ('rust','python') and stem.startswith('repair-'):
                card['target_answer']=s['answer']
            writes.append(card)
        # Only retain parameters actually used (and their dependency closure).
        for q in qs+writes:
            used=set(re.findall(r'\$\{(\w+)\}',json.dumps({k:v for k,v in q.items() if k not in ('parameters','derived')})))
            derived={k:v for k,v in DERIVED.items() if k in used}
            for formula in derived.values():
                used.update(re.findall(r'\b[a-z]+\b',formula))
            q['parameters']={k:v for k,v in PARAMS.items() if k in used}
            q['derived']=derived
            if not q['parameters']: q.pop('parameters');q.pop('derived')
        data['lessons'].append(dict(id=l['id'],title=l['title'],section=l.get('section','Basics' if index<5 else 'Intermediate' if index<10 else 'Advanced'),
            intro=baseline+'. '+l['notes']+'\n\nRead each snippet, identify its effect, then complete a fragment. Examples are independent unless stated otherwise. '+
                  'Snippets may omit surrounding entry points and standard imports; displayed code is never executed by the tutor.',
            sources=l.get('sources',[s['id'] for s in sources]),requires=[] if index==0 else [lessons[index-1]['id']],questions=qs+writes))
    (ROOT/'codelingo/courses'/f'{cid}.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')

def source(cid,title,url):
    return dict(id=cid,title=title,url=url,usage='Curriculum and language-behavior reference. Code Lingo explanations and exercises are newly authored; source assignments and prose are not reproduced.')

if __name__=='__main__':
    import sys
    sys.path.insert(0,str(Path(__file__).parent))
    from imperative import build as imperative
    from systems import build as systems
    from web_types import build as web_types
    from sql_course import build as sql_course
    imperative();systems();web_types();sql_course()
    from catalog import write_catalog
    write_catalog()
