"""Simulated strategies, not measured human win rates. Run from Bot.
python tests/simulate_triple_triad_balance.py --matches 1000 --output balance.json
"""
import argparse,json,random,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from crystal_guild import gold_saucer as g
p=argparse.ArgumentParser();p.add_argument('--matches',type=int,default=1000);p.add_argument('--output');args=p.parse_args()
rng=random.Random(135);sides=('top','right','bottom','left')
def play(deck,o,strategy):
 board=[None]*9;hand=list(deck);npc=list(o['deck']);seed=str(rng.getrandbits(64))
 while None in board:
  moves=[(c,i) for c in hand for i,x in enumerate(board) if x is None]
  if strategy=='random':c,i=rng.choice(moves)
  else:
   ranked=[]
   for c,i in moves:
    trial=[dict(x) if x else None for x in board];cap=len(g.triple_triad_place(trial,i,c,'player'));r,co=divmod(i,3)
    exposed=[side for side,j,legal in [('top',i-3,r>0),('right',i+1,co<2),('bottom',i+3,r<2),('left',i-1,co>0)] if legal and trial[j] is None]
    protect=sum(g.TRIPLE_TRIAD_CARDS_BY_ID[c][s] for s in exposed)/max(1,len(exposed))
    ranked.append((cap*8+protect*.6+rng.random()*2,c,i))
   _,c,i=max(ranked)
  g.triple_triad_place(board,i,c,'player');hand.remove(c)
  if None not in board:break
  c,i=g.triple_triad_npc_move(board,npc,o['difficulty'],seed);g.triple_triad_place(board,i,c,'npc');npc.remove(c)
 ps,ns=g.triple_triad_score(board);ps+=len(hand);ns+=len(npc)
 return 'win' if ps>ns else 'draw' if ps==ns else 'loss'
report=[]
for o in g.TRIPLE_TRIAD_OPPONENTS:
 tier={'Novice':1,'Standard':1,'Skilled':2,'Expert':3,'Master':4}[o['difficulty']]
 deck=list(g.TRIPLE_TRIAD_STARTER_DECK) if tier==1 and o['difficulty']=='Novice' else [c['id'] for c in sorted([c for c in g.TRIPLE_TRIAD_CARDS if c['rarity']<=tier],key=lambda c:-sum(c[s] for s in sides))[:5]]
 for strategy in (['random','basic'] if o['difficulty']=='Novice' else ['basic']):
  results=[play(deck,o,strategy) for _ in range(args.matches)]
  report.append(dict(opponent=o['id'],difficulty=o['difficulty'],strategy=strategy,deck=deck,matches=args.matches,**{k:round(results.count(k)*100/args.matches,1) for k in ['win','draw','loss']}))
s=json.dumps(report,indent=2);print(s)
if args.output:Path(args.output).write_text(s+'\n')
