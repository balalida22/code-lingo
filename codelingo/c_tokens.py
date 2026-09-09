"""Conservative C/C++ fragment comparison, without compiling or executing.

Ignore whitespace between tokens, never within literals or compound operators.
Preprocessor directives, comments, and line splicing keep exact matching because
their whitespace/newline rules need additional preprocessing context.
"""
import re

IDENT=r'(?:[^\W\d]|_)\w*'
RAW=re.compile(r'(?:u8|u|U|L)?R"([^\s()\\]{0,16})\(.*?\)\1"'+r'(?:'+IDENT+r')?',re.DOTALL)
QUOTED=re.compile(r'''(?:u8|u|U|L)?(?:"(?:\\[^\r\n]|[^"\\\r\n])*"|'(?:\\[^\r\n]|[^'\\\r\n])*')'''+r'(?:'+IDENT+r')?')
NUMBER=re.compile(r"(?:[0-9]|\.[0-9])(?:[eEpP][+-]|[\w.]|'\w)*")
NAME=re.compile(IDENT)
OPERATORS=sorted(('>>=','<<=','<=>','->*','...','%:%:','##','::','.*','++','--','->',
 '&&','||','<=','>=','==','!=','*=','/=','%=','+=','-=','&=','^=','|=','<<','>>',
 '<:',':>','<%','%>','%:')+tuple('{}[]().,:;?~!%^&*+-/|<>=#'),key=len,reverse=True)

def tokens(text):
    if len(text)>2000:
        raise ValueError('Answer is too long')
    result=[];position=0
    while position<len(text):
        if text[position].isspace():
            position+=1;continue
        if text.startswith(('//','/*','\\'),position):
            raise ValueError('Preprocessing-sensitive fragment requires exact matching')
        match=None
        for pattern in (RAW,QUOTED,NUMBER,NAME):
            match=pattern.match(text,position)
            if match:break
        if match:
            token=match.group();position=match.end()
        else:
            token=next((op for op in OPERATORS if text.startswith(op,position)),None)
            if token is None:raise ValueError('Unrecognized token')
            position+=len(token)
        if token in ('#','##','%:','%:%:'):
            raise ValueError('Preprocessor fragment requires exact matching')
        result.append(token)
    return tuple(result)

def equivalent(answer,expected):
    if len(answer)>2000:return False
    if answer.strip()==expected.strip():return True
    try:return tokens(answer)==tokens(expected)
    except ValueError:return False
