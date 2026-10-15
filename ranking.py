"""Core logic for interactive pairwise ranking; no Streamlit dependency."""
from dataclasses import dataclass
@dataclass
class NeedComparison(Exception):
    a:int
    b:int

def relation(a,b,history,n_alternatives):
    if a==b:return 0
    direct={}
    for h in history:
        x,y,r=h['a'],h['b'],h['result'];direct[(x,y)]=r;direct[(y,x)]=2 if r==1 else 1 if r==2 else 0
    if (a,b) in direct:return direct[(a,b)]
    parent=list(range(n_alternatives))
    def find(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    def union(x,y):
        x,y=find(x),find(y)
        if x!=y:parent[y]=x
    for h in history:
        if h['result']==0:union(h['a'],h['b'])
    comp=[find(i) for i in range(n_alternatives)]
    if comp[a]==comp[b]:return 0
    roots=sorted(set(comp));ri={x:i for i,x in enumerate(roots)};g=[[False]*len(roots) for _ in roots]
    for h in history:
        x,y,r=h['a'],h['b'],h['result'];better,worse=(x,y) if r==1 else ((y,x) if r==2 else (None,None))
        if better is not None and comp[better]!=comp[worse]:g[ri[comp[better]]][ri[comp[worse]]]=True
    for k in range(len(roots)):
        for i in range(len(roots)):
            if g[i][k]:
                for j in range(len(roots)):g[i][j]=g[i][j] or g[k][j]
    x,y=ri[comp[a]],ri[comp[b]];ab,ba=g[x][y],g[y][x]
    if ab and not ba:return 1
    if ba and not ab:return 2
    return None

def merge_sort_interactive(items,history,n_alternatives=None):
    if n_alternatives is None:n_alternatives=max(items+[0])+1
    if len(items)<=1:return list(items)
    mid=len(items)//2;l=merge_sort_interactive(items[:mid],history,n_alternatives);r=merge_sort_interactive(items[mid:],history,n_alternatives);out=[];i=j=0
    while i<len(l) and j<len(r):
        rel=relation(l[i],r[j],history,n_alternatives)
        if rel is None:raise NeedComparison(l[i],r[j])
        if rel==1:out.append(l[i]);i+=1
        elif rel==2:out.append(r[j]);j+=1
        else:out.extend([l[i],r[j]]);i+=1;j+=1
    return out+l[i:]+r[j:]
