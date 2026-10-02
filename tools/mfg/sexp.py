import re
def parse(text):
    tok=re.compile(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()"]+')
    stack=[[]]
    for m in tok.finditer(text):
        t=m.group(0)
        if t=='(':
            stack.append([])
        elif t==')':
            l=stack.pop(); stack[-1].append(l)
        else:
            if t[0]=='"': t=bytes(t[1:-1],'utf-8').decode('unicode_escape') if '\\' in t else t[1:-1]
            stack[-1].append(t)
    return stack[0][0]
def find(node,name):
    return [c for c in node if isinstance(c,list) and c and c[0]==name]
def prop(node,name):
    for c in find(node,'property'):
        if c[1]==name: return c[2]
