#!/usr/bin/env python3
"""Moteur de fusion de la veille maison.
Usage:  python3 scan/engine.py [--date AAAA-MM-JJ] [--dry]
Lit data/*.json et scan/runs/d_*.json (deltas produits par scan/lib.js dans le navigateur), applique:
 - mise à jour des prix par lien et de l'historique, - ajout de liens (doublons fusionnés), - promotion des indicateurs (cave, 2 logements),
 - création des nouvelles annonces (avec règles d'exclusion), - date de relève par source (meta.json).
Les deltas appliqués sont déplacés dans scan/runs/done/."""
import json,sys,os,glob,shutil,datetime,collections
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D=lambda p:os.path.join(ROOT,p)
args=sys.argv[1:]
TODAY=args[args.index('--date')+1] if '--date' in args else datetime.date.today().isoformat()
DRY='--dry' in args
L=json.load(open(D('data/listings.json')));P=json.load(open(D('data/prices.json')));M=json.load(open(D('data/meta.json')))
DRIVE={'Caissargues':10,'Bouillargues':12,'Rodilhan':15,'Garons':15,'Redessan':15,'Manduel':15,'Générac':20,'Bellegarde':25}
PFX={"Bien'ici":'bi','Leboncoin':'lbc','SeLoger':'sl','Orpi':'orpi','AVendreALouer':'av','PAP':'pap','Notaires':'notaires'}
QD={}
for x in L:
    if x.get('q') and x.get('de') and (x['c'],x['q']) not in QD: QD[(x['c'],x['q'])]=(x['dc'],x['dl'])
log=collections.Counter();notes=[]
def hist(k,x):
    h=P['items'].setdefault(k,[[None,x['p']]] if False else [])
    if not h: h.append([TODAY,x['p']])
    return h
def set_price(x,newp,why):
    if newp==x['p']:return
    h=hist(x['k'],x)
    if h[-1][1]!=x['p']: h.append([TODAY,x['p']])
    old=x['p'];x['p']=newp;h.append([TODAY,newp])
    if newp<old:x['pd']=1
    log['prix modifié']+=1;notes.append(f"{x['k']} {x['c']}: {old} → {newp} ({why})")
def dist(c,q):
    if (c,q) in QD:return QD[(c,q)]+(1,)
    if c=='Nîmes':return ('inconnue','Quartier non précisé, distance à la gare inconnue',0)
    t=DRIVE[c];return ('voiture' if t<=15 else 'loin','Estimation: ≈ %d min en voiture de la gare de Nîmes'%t,1)
def exclusion(n,f):
    c=n['c']
    if f.get('vi'):return 'Viager ou nue-propriété'
    if n['p']<120000:return 'Prix anormalement bas (viager, bouquet ou erreur ?) à vérifier'
    if f.get('rx'):return 'Rénovation importante à prévoir'
    if f.get('ms'):return 'Construction à venir ou sans permis de construire mentionné'
    if f.get('ur'):
        if c=='Nîmes' and not f.get('jd'):return 'Maison de ville sans vrai jardin'
        if c!='Nîmes' and f.get('mi')!='n' and not f.get('jd'):return 'Maison de ville ou de village sans vrai jardin'
    return ''
files=sorted(glob.glob(D('scan/runs/d_*.json')))
if not files:print('aucun delta à appliquer');sys.exit(0)
seen=set()
for fn in files:
    d=json.load(open(fn));src=d['src']
    for i,lab,url,p in d['lk']:
        x=L[i]
        if not any(u[1]==url for u in x['u']):x['u'].append([lab,url,p]);log['liens ajoutés']+=1
    for i,url,newp,oldp in d['pp']:
        x=L[i]
        for u in x['u']:
            if u[1]==url:
                prev=u[2] if len(u)>2 else None;u[:]=[u[0],u[1],newp]
                real=(prev and prev!=newp) or (not prev and abs(x['p']-newp)>2000)
                if real:
                    pr=[v[2] for v in x['u'] if len(v)>2 and v[2]]
                    set_price(x,min(pr) if pr else newp,src)
    for i,up in d['up']:
        x=L[i]
        for k,v in up.items():
            if k=='lg' and v>x.get('lg',0):x['lg']=v;log['2 logements détectés']+=1
            elif k=='ca' and not x.get('ca'):x['ca']=1;log['cave détectée']+=1
            elif k=='vi':notes.append(f"VIAGER possible: {x['k']} {x['c']}")
    seen.update(d['seen']);seen.update(i for i,*_ in d['lk'])
    for n in d['nw']:
        f=dict(ca=0,lg=0,g='?',pi='n',cl=0,mi='?',bu=0,pl=0,p2=0,tr='n',jd=0,vi=0,ms=0,ur=0,rx=0);f.update(n['f']);c=n['c'];k=PFX.get(n['s'],n['s'][:3].lower())+'-'+n['id'].replace('/','_')
        if any(x['k']==k for x in L):continue
        dc,dl,de=dist(c,n['q'])
        ex=exclusion(n,f)
        x=dict(k=k,c=c,q=n['q'],p=n['p'],o=0,a=n['a'],l=n['l'],r=n['r'],b=n['b'],be=0,dpe=n['dpe'],y=n['y'],g=f['g'],gm=0,cl=f['cl'],pi=f['pi'],ca=f['ca'],mi=f['mi'],bu=f['bu'],tr=f['tr'],pl=f['pl'],p2=f['p2'],pd=1 if n.get('dec') else 0,pa=0,pub=n['pub'] if n['pub']!='1970-01-01' else '',mod=n['mod'],dc=dc,dl=dl,de=de,u=[[n['s'],n['url'],n['p']]],grp='A' if c=='Nîmes' else 'B',st='',pm=0,vi=f['vi'],ms=f['ms'],jd=f['jd'],jt=0,te=0,tx=1,ex=ex,ur=f['ur'],lg=f['lg'],sd=TODAY)
        L.append(x);P['items'][k]=[[TODAY,n['p']]];log['nouvelles annonces']+=1
        notes.append(f"NOUVEAU {k} {c} {n['p']} € {n['a']} m²"+(f" [exclu: {ex}]" if ex else ''))
    for s in M['sources']:
        if s['n'].startswith(src.split(' ')[0]):s['st']='ok';s['d']=TODAY
    if not DRY:
        os.makedirs(D('scan/runs/done'),exist_ok=True);shutil.move(fn,D('scan/runs/done/'+TODAY+'_'+os.path.basename(fn)))
for i in seen:L[i]['sd']=TODAY
P['scan']=TODAY
if not DRY:
    json.dump(L,open(D('data/listings.json'),'w'),ensure_ascii=False,separators=(',',':'))
    json.dump(P,open(D('data/prices.json'),'w'),ensure_ascii=False,separators=(',',':'))
    json.dump(M,open(D('data/meta.json'),'w'),ensure_ascii=False,indent=1)
print(dict(log));print('\n'.join(notes))
print('total annonces:',len(L))
