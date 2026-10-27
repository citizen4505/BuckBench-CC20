import json,sys
from sexp import parse, find, find1
d=sys.argv[1]; p=sys.argv[2]
want=json.load(open(f'{d}/netpins.json'))
t=parse(open(f'{d}/{p}.net').read())
got={}
for n in find(find1(t,'nets'),'net'):
    got[find1(n,'name')[1].lstrip('/')]=frozenset(f"{find1(x,'ref')[1]}.{find1(x,'pin')[1]}" for x in find(n,'node'))
gs={v for k,v in got.items() if not k.startswith('unconnected')}
ws={frozenset(v) for v in want.values()}
print('missing', [sorted(x) for x in ws-gs]); print('extra', [sorted(x) for x in gs-ws])
print('nets', len(ws), 'ok' if ws==gs else 'FAIL', 'NC pins', sum(k.startswith('unconnected') for k in got))
