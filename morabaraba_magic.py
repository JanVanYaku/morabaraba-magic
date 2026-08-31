#!/usr/bin/env python3
import math, random, sys
import pygame

W,H,FPS=1180,760,60
BG=(18,27,31); PANEL=(31,43,47); PARCH=(244,222,164); LINE=(55,39,24)
TEXT=(245,242,233); MUTED=(180,187,185); GOLD=(236,176,66)
RED=(216,66,65); BLUE=(55,135,205); WHITE=(255,255,255); GREEN=(90,184,120)
EMPTY,REDP,BLUEP=0,1,2
NAMES={REDP:"Red",BLUEP:"Blue"}

OUT=[(0,0),(3,0),(6,0),(6,3),(6,6),(3,6),(0,6),(0,3)]
MID=[(1,1),(3,1),(5,1),(5,3),(5,5),(3,5),(1,5),(1,3)]
INN=[(2,2),(3,2),(4,2),(4,3),(4,4),(3,4),(2,4),(2,3)]
CTR=(3,3)

def ring(r):
    return [(r[i],r[(i+1)%8]) for i in range(8)]

def make_board(center,margin,protect,name,subtitle):
    pts=OUT+MID+INN+([CTR] if center else [])
    edges=ring(OUT)+ring(MID)+ring(INN)
    for a,b,c in [((3,0),(3,1),(3,2)),((6,3),(5,3),(4,3)),
                  ((3,6),(3,5),(3,4)),((0,3),(1,3),(2,3))]:
        edges += [(a,b),(b,c)]
    edges += [((0,0),(1,1)),((6,0),(5,1)),((6,6),(5,5)),((0,6),(1,5))]
    mills=[
        ((0,0),(3,0),(6,0)),((6,0),(6,3),(6,6)),((0,6),(3,6),(6,6)),((0,0),(0,3),(0,6)),
        ((1,1),(3,1),(5,1)),((5,1),(5,3),(5,5)),((1,5),(3,5),(5,5)),((1,1),(1,3),(1,5)),
        ((2,2),(3,2),(4,2)),((4,2),(4,3),(4,4)),((2,4),(3,4),(4,4)),((2,2),(2,3),(2,4)),
        ((3,0),(3,1),(3,2)),((6,3),(5,3),(4,3)),((3,6),(3,5),(3,4)),((0,3),(1,3),(2,3))
    ]
    if center:
        edges += [((3,2),CTR),(CTR,(3,4)),((2,3),CTR),(CTR,(4,3))]
        mills += [((3,2),CTR,(3,4)),((2,3),CTR,(4,3))]
    idx={p:i for i,p in enumerate(pts)}
    e=[(idx[a],idx[b]) for a,b in edges]
    m=[tuple(idx[x] for x in q) for q in mills]
    adj={i:set() for i in range(len(pts))}
    for a,b in e: adj[a].add(b); adj[b].add(a)
    return dict(name=name,subtitle=subtitle,pts=pts,edges=e,mills=m,adj=adj,
                margin=margin,protect=protect)

BOARDS=[
    make_board(True,.025,False,"Board 1","Koti / Sesotho • 25 points"),
    make_board(False,.075,True,"Board 2","Open Centre • 24 points"),
    make_board(True,.075,False,"Board 3","Koti Compact • 25 points"),
]

def opp(p): return BLUEP if p==REDP else REDP
def count(b,p): return sum(x==p for x in b)

def in_mill(cfg,b,pos,p):
    return any(pos in m and all(b[x]==p for x in m) for m in cfg["mills"])

def captures(cfg,b,victim):
    xs=[i for i,x in enumerate(b) if x==victim]
    if not cfg["protect"]: return xs
    free=[i for i in xs if not in_mill(cfg,b,i,victim)]
    return free or xs

def legal(cfg,b,hand,p):
    empt=[i for i,x in enumerate(b) if x==EMPTY]
    if hand[p]>0: return [(None,d) for d in empt]
    own=[i for i,x in enumerate(b) if x==p]
    if len(own)==3: return [(s,d) for s in own for d in empt]
    return [(s,d) for s in own for d in cfg["adj"][s] if b[d]==EMPTY]

def threats(cfg,b,p):
    out=set()
    for m in cfg["mills"]:
        vals=[b[x] for x in m]
        if vals.count(p)==2 and vals.count(EMPTY)==1:
            out.add(m[vals.index(EMPTY)])
    return out

def ai_move(cfg,b,hand,p):
    moves=legal(cfg,b,hand,p)
    if not moves: return None
    enemy=opp(p); block=threats(cfg,b,enemy)
    scored=[]
    for s,d in moves:
        bb=b[:]; hh=dict(hand)
        if s is None: bb[d]=p; hh[p]-=1
        else: bb[s]=EMPTY; bb[d]=p
        sc=random.random()*4
        if in_mill(cfg,bb,d,p): sc+=10000
        if d in block: sc+=2500
        sc += len(threats(cfg,bb,p))*150 - len(threats(cfg,bb,enemy))*120
        sc += len(cfg["adj"][d])*20
        scored.append((sc,s,d))
    scored.sort(reverse=True)
    return scored[0][1],scored[0][2]

class Game:
    def __init__(self):
        self.mode="ai"; self.cfg=BOARDS[0]; self.started=False; self.reset()
    def reset(self):
        self.b=[EMPTY]*len(self.cfg["pts"]); self.hand={REDP:12,BLUEP:12}
        self.turn=REDP; self.sel=None; self.capture=False; self.winner=None
        self.status="Red places the first cow."; self.ai_since=None
    def start(self,mode,cfg):
        self.mode=mode; self.cfg=cfg; self.started=True; self.reset()
    def placement(self): return self.hand[REDP]>0 or self.hand[BLUEP]>0
    def phase(self,p):
        if self.placement(): return "Placement"
        return "Flying" if count(self.b,p)==3 else "Movement"
    def human_turn(self): return self.mode=="local" or self.turn==REDP
    def finish(self,d):
        if in_mill(self.cfg,self.b,d,self.turn):
            self.capture=True; self.sel=None
            self.status=f"{NAMES[self.turn]} formed a mill. Capture a cow."
        else: self.end()
    def end(self):
        self.sel=None; self.capture=False
        nxt=opp(self.turn)
        if not self.placement():
            if count(self.b,nxt)<3 or not legal(self.cfg,self.b,self.hand,nxt):
                self.winner=self.turn; self.status=f"{NAMES[self.turn]} wins!"; return
        self.turn=nxt; self.ai_since=None
        self.status=f"{NAMES[self.turn]}'s turn: {self.phase(self.turn).lower()}."
    def click(self,pos):
        if not self.started or self.winner or not self.human_turn() or pos is None: return
        if self.capture:
            if pos in captures(self.cfg,self.b,opp(self.turn)):
                self.b[pos]=EMPTY; self.end()
            return
        if self.placement():
            if self.b[pos]==EMPTY:
                self.b[pos]=self.turn; self.hand[self.turn]-=1; self.finish(pos)
            return
        if self.sel is None:
            if self.b[pos]==self.turn: self.sel=pos
            return
        if pos==self.sel: self.sel=None; return
        if self.b[pos]==self.turn: self.sel=pos; return
        s=self.sel; self.sel=None
        if self.b[pos]!=EMPTY: return
        if count(self.b,self.turn)!=3 and pos not in self.cfg["adj"][s]:
            self.status="That destination is not connected."; return
        self.b[s]=EMPTY; self.b[pos]=self.turn; self.finish(pos)
    def ai_tick(self):
        if self.mode!="ai" or self.turn!=BLUEP or self.winner: self.ai_since=None; return
        now=pygame.time.get_ticks()
        if self.ai_since is None: self.ai_since=now; return
        if now-self.ai_since<450: return
        if self.capture:
            xs=captures(self.cfg,self.b,REDP)
            if xs: self.b[random.choice(xs)]=EMPTY
            self.end(); return
        mv=ai_move(self.cfg,self.b,self.hand,BLUEP)
        if not mv: self.winner=REDP; return
        s,d=mv
        if s is None: self.b[d]=BLUEP; self.hand[BLUEP]-=1
        else: self.b[s]=EMPTY; self.b[d]=BLUEP
        self.ai_since=now; self.finish(d)

class App:
    def __init__(self):
        pygame.init(); pygame.display.set_caption("Morabaraba Magic")
        self.s=pygame.display.set_mode((W,H)); self.clock=pygame.time.Clock()
        self.f=pygame.font.SysFont("segoeui",20); self.fb=pygame.font.SysFont("segoeui",21,bold=True)
        self.big=pygame.font.SysFont("georgia",42,bold=True); self.game=Game()
        self.screen="menu"; self.pending="ai"; self.choice=0
    def txt(self,t,font,color,pos,center=False):
        x=font.render(t,True,color); r=x.get_rect(center=pos) if center else x.get_rect(topleft=pos); self.s.blit(x,r)
    def button(self,r,t,accent=False):
        m=pygame.mouse.get_pos(); c=GOLD if accent else PANEL
        if r.collidepoint(m): c=tuple(min(255,x+18) for x in c)
        pygame.draw.rect(self.s,c,r,border_radius=12); pygame.draw.rect(self.s,(80,92,95),r,2,border_radius=12)
        self.txt(t,self.fb,(15,15,15) if accent else TEXT,r.center,True)
    def menu(self):
        self.s.fill(BG); self.txt("MORABARABA MAGIC",self.big,GOLD,(W//2,105),True)
        self.txt("Traditional strategy, three board choices.",self.f,MUTED,(W//2,175),True)
        rs=[pygame.Rect(W//2-170,300+i*72,340,55) for i in range(4)]
        labs=["Play vs Computer","Two Players","How to Play","Quit"]
        for i,(r,l) in enumerate(zip(rs,labs)): self.button(r,l,i==0)
        return rs
    def preview(self,cfg,r):
        pygame.draw.rect(self.s,PARCH,r)
        def p(c):
            gx,gy=c; mar=r.width*cfg["margin"]+12; use=r.width-2*mar
            return int(r.x+mar+gx/6*use),int(r.y+mar+gy/6*use)
        for a,b in cfg["edges"]:
            pygame.draw.line(self.s,LINE,p(cfg["pts"][a]),p(cfg["pts"][b]),2)
        for c in cfg["pts"]: pygame.draw.circle(self.s,LINE,p(c),4)
    def choose(self):
        self.s.fill(BG); self.txt("Choose Your Board",self.big,GOLD,(W//2,70),True)
        cards=[pygame.Rect(45+i*380,170,330,410) for i in range(3)]
        for i,(cfg,r) in enumerate(zip(BOARDS,cards)):
            pygame.draw.rect(self.s,PANEL,r,border_radius=16)
            pygame.draw.rect(self.s,GOLD if i==self.choice else (75,85,88),r,4 if i==self.choice else 2,border_radius=16)
            self.preview(cfg,pygame.Rect(r.x+25,r.y+25,280,250))
            self.txt(cfg["name"],self.fb,TEXT,(r.x+24,r.y+300))
            self.txt(cfg["subtitle"],self.f,MUTED,(r.x+24,r.y+334))
            rule="Any cow capturable" if not cfg["protect"] else "Mill cows protected"
            self.txt(rule,self.f,GOLD,(r.x+24,r.y+370))
        back=pygame.Rect(45,640,150,52); go=pygame.Rect(W//2-170,640,340,52)
        self.button(back,"Back"); self.button(go,"Continue",True)
        return cards,back,go
    def geom(self,i):
        c=self.game.cfg["pts"][i]; gx,gy=c; mar=630*self.game.cfg["margin"]; use=630-2*mar
        return int(55+mar+gx/6*use),int(75+mar+gy/6*use)
    def hit(self,pos):
        best=None; dist=32
        for i in range(len(self.game.b)):
            x,y=self.geom(i); d=math.hypot(pos[0]-x,pos[1]-y)
            if d<dist: best=i; dist=d
        return best
    def game_screen(self):
        self.s.fill(BG); br=pygame.Rect(32,52,676,676); pygame.draw.rect(self.s,PARCH,br,border_radius=14)
        for a,b in self.game.cfg["edges"]: pygame.draw.line(self.s,LINE,self.geom(a),self.geom(b),4)
        for i in range(len(self.game.b)):
            x,y=self.geom(i); pygame.draw.circle(self.s,LINE,(x,y),8)
        if self.game.sel is not None:
            x,y=self.geom(self.game.sel); pygame.draw.circle(self.s,GOLD,(x,y),30,4)
        if self.game.capture:
            for i in captures(self.game.cfg,self.game.b,opp(self.game.turn)):
                x,y=self.geom(i); pygame.draw.circle(self.s,GOLD,(x,y),30,4)
        for i,v in enumerate(self.game.b):
            if v:
                x,y=self.geom(i); col=RED if v==REDP else BLUE
                pygame.draw.circle(self.s,(70,50,35),(x+4,y+5),24); pygame.draw.circle(self.s,col,(x,y),22)
                pygame.draw.circle(self.s,WHITE,(x,y),22,2)
        pr=pygame.Rect(750,45,390,665); pygame.draw.rect(self.s,PANEL,pr,border_radius=18)
        self.txt("Morabaraba Magic",self.fb,GOLD,(775,70)); self.txt(self.game.cfg["subtitle"],self.f,MUTED,(775,105))
        y=155
        for p in (REDP,BLUEP):
            self.txt(NAMES[p]+(" (Computer)" if self.game.mode=="ai" and p==BLUEP else ""),self.fb,TEXT,(775,y))
            self.txt(f"On board: {count(self.game.b,p)}   In hand: {self.game.hand[p]}",self.f,MUTED,(775,y+32)); y+=95
        self.txt("PHASE",self.f,MUTED,(775,355)); self.txt(self.game.phase(self.game.turn),self.fb,GOLD,(775,383))
        self.txt("STATUS",self.f,MUTED,(775,445))
        words=self.game.status.split(); line=""; yy=475
        for w in words:
            test=(line+" "+w).strip()
            if self.f.size(test)[0]>330:
                self.txt(line,self.f,TEXT,(775,yy)); yy+=25; line=w
            else: line=test
        if line:self.txt(line,self.f,TEXT,(775,yy))
        nr=pygame.Rect(775,630,150,45); br2=pygame.Rect(945,630,150,45)
        self.button(nr,"New Game",True); self.button(br2,"Boards")
        if self.game.winner:
            ov=pygame.Surface((W,H),pygame.SRCALPHA); ov.fill((0,0,0,170)); self.s.blit(ov,(0,0))
            self.txt(f"{NAMES[self.game.winner]} wins!",self.big,GOLD,(W//2,H//2),True)
        return nr,br2
    def rules(self):
        self.s.fill(BG); self.txt("How to Play",self.big,GOLD,(60,50))
        lines=[
            "Each player starts with 12 cows.",
            "Placement: alternate placing cows on empty points.",
            "Mill: three cows on a valid line. Forming one earns a capture.",
            "Movement: after placement, move to an adjacent connected empty point.",
            "Flying: with exactly three cows left, move to any empty point.",
            "Board 1 and 3: centre is active; any opponent cow may be captured.",
            "Board 2: open centre; cows in mills are protected unless all are in mills.",
            "Win by reducing the opponent to two cows or blocking all legal moves."
        ]
        y=145
        for x in lines:self.txt("• "+x,self.f,TEXT,(80,y)); y+=48
        r=pygame.Rect(60,660,150,50); self.button(r,"Back",True); return r
    def run(self):
        while True:
            self.clock.tick(FPS)
            menu_rs=cards=back=go=nr=br2=rr=None
            if self.screen=="menu": menu_rs=self.menu()
            elif self.screen=="choose": cards,back,go=self.choose()
            elif self.screen=="game": nr,br2=self.game_screen()
            else: rr=self.rules()
            pygame.display.flip()
            for e in pygame.event.get():
                if e.type==pygame.QUIT: pygame.quit(); return
                if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE:
                    self.screen="menu" if self.screen!="menu" else self.screen
                if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                    p=e.pos
                    if self.screen=="menu":
                        for i,r in enumerate(menu_rs):
                            if r.collidepoint(p):
                                if i==0:self.pending="ai";self.screen="choose"
                                elif i==1:self.pending="local";self.screen="choose"
                                elif i==2:self.screen="rules"
                                else:pygame.quit();return
                    elif self.screen=="choose":
                        for i,r in enumerate(cards):
                            if r.collidepoint(p):self.choice=i
                        if back.collidepoint(p):self.screen="menu"
                        if go.collidepoint(p):self.game.start(self.pending,BOARDS[self.choice]);self.screen="game"
                    elif self.screen=="game":
                        if nr.collidepoint(p):self.game.start(self.game.mode,self.game.cfg)
                        elif br2.collidepoint(p):self.pending=self.game.mode;self.screen="choose"
                        else:self.game.click(self.hit(p))
                    else:
                        if rr.collidepoint(p):self.screen="menu"
            if self.screen=="game": self.game.ai_tick()

if __name__=="__main__":
    App().run()
