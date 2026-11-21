"""İki hash-pinned yerel Ollama Go şablonu için sınırlı, ağsız renderer.

Genel Go yorumlayıcısı değildir. Tool/image/generation yok; bilinmeyen sözdizimi
reddedilir. Kaynak content değerlendirilmez, yalnız veri olarak eklenir.
"""
import json
import re

WS=' \t\r\n'


def lex(template):
    items=[];at=0;trim_next=False
    for match in re.finditer(r'{{(.*?)}}',template,re.S):
        content=template[at:match.start()];action=match.group(1)
        if trim_next:content=content.lstrip(WS)
        if action.startswith('-'):content=content.rstrip(WS);action=action[1:]
        trim_next=action.endswith('-')
        if trim_next:action=action[:-1]
        if content:items.append(('text',content))
        items.append(('action',action.strip()));at=match.end()
    tail=template[at:]
    if trim_next:tail=tail.lstrip(WS)
    if tail:items.append(('text',tail))
    return items


def parse(template):
    root=[];current=root;stack=[]
    for kind,code in lex(template):
        if kind=='text':current.append(('text',code));continue
        if code.startswith('if '):
            node={'kind':'if','branches':[(code[3:],[])]};current.append(node)
            stack.append((current,node));current=node['branches'][0][1]
        elif code.startswith('range '):
            node={'kind':'range','expr':code[6:],'body':[]};current.append(node)
            stack.append((current,node));current=node['body']
        elif code.startswith('else'):
            if not stack or stack[-1][1]['kind']!='if':raise ValueError('unsupported else')
            node=stack[-1][1];condition=code[8:] if code.startswith('else if ') else None
            if code!='else' and condition is None:raise ValueError('unsupported else syntax')
            node['branches'].append((condition,[]));current=node['branches'][-1][1]
        elif code=='end':
            if not stack:raise ValueError('unmatched end')
            current,_=stack.pop()
        else:current.append(('action',code))
    if stack:raise ValueError('unclosed template block')
    return root


def evaluate(expression,dot,root,scopes):
    tokens=re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',expression);at=0
    def value():
        nonlocal at
        if at>=len(tokens):raise ValueError('missing expression')
        token=tokens[at];at+=1
        if token=='(':
            ans=value()
            if at>=len(tokens) or tokens[at]!=')':raise ValueError('expression parentheses')
            at+=1;return ans
        if token in ['eq','ne']:
            left=value();right=value();return (left==right) if token=='eq' else (left!=right)
        if token in ['and','or']:
            args=[]
            while at<len(tokens) and tokens[at]!=')':args.append(value())
            return all(args) if token=='and' else any(args)
        if token=='len':return len(value())
        if token=='slice':
            data=value();start=value();return data[start:]
        if token.startswith('"'):return json.loads(token)
        if re.fullmatch(r'-?\d+',token):return int(token)
        if token=='.':return dot
        if token.startswith('$.'):return root.get(token[2:])
        if token.startswith('.'):
            out=dot
            for name in token[1:].split('.'):
                out=out.get(name) if isinstance(out,dict) else None
            return out
        if token.startswith('$'):
            base,*fields=token.split('.')
            for scope in reversed(scopes):
                if base in scope:
                    out=scope[base]
                    for field in fields:out=out.get(field) if isinstance(out,dict) else None
                    return out
            raise ValueError('undefined variable: '+token)
        raise ValueError('unsupported template expression: '+token)
    result=value()
    if at!=len(tokens):raise ValueError('unconsumed expression: '+expression)
    return result


def execute(template,messages):
    if any(m['role'] not in ['system','user'] or set(m)!={'role','content'} for m in messages):
        raise ValueError('only plain system/user input supported')
    # Ollama0.40.6 collate: system koleksiyonu ayrıdır, system mesajı listede kalır.
    collated=[];systems=[]
    for m in messages:
        if m['role']=='system':systems.append(m['content'])
        if collated and collated[-1]['Role']==m['role']:collated[-1]['Content']+='\n\n'+m['content']
        else:collated.append({'Role':m['role'],'Content':m['content'],'ToolCalls':[]})
    root={'Messages':collated,'System':'\n\n'.join(systems),'Tools':[],'Think':False,'IsThinkSet':True}
    def render(nodes,dot,scopes):
        result=[]
        for node in nodes:
            if isinstance(node,tuple):
                kind,code=node
                if kind=='text':result.append(code);continue
                assignment=re.fullmatch(r'(\$\w+)\s*(:=|=)\s*(.*)',code,re.S)
                if assignment:
                    name,op,expr=assignment.groups();v=evaluate(expr,dot,root,scopes)
                    if op==':=':scopes[-1][name]=v
                    else:
                        target=next((s for s in reversed(scopes) if name in s),None)
                        if target is None:raise ValueError('assignment to undefined variable')
                        target[name]=v
                else:
                    v=evaluate(code,dot,root,scopes)
                    result.append('' if v is None else str(v))
            elif node['kind']=='if':
                for condition,body in node['branches']:
                    if condition is None or evaluate(condition,dot,root,scopes):
                        result.append(render(body,dot,scopes+[{}]));break
            elif node['kind']=='range':
                expression=node['expr'];names=[]
                if ':=' in expression:
                    binding,expression=expression.split(':=',1);names=[x.strip() for x in binding.split(',')]
                data=evaluate(expression.strip(),dot,root,scopes)
                for i,item in enumerate(data or []):
                    local={}
                    if len(names)==1:local[names[0]]=item
                    elif len(names)==2:local.update({names[0]:i,names[1]:item})
                    elif names:raise ValueError('unsupported range binding')
                    result.append(render(node['body'],item,scopes+[local]))
            else:raise ValueError('unsupported node')
        return ''.join(result)
    return render(parse(template),root,[{}])
