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
PFX={"Bien'ici":'bi','Leboncoin':'lbc','SeLoger':'sl','Orpi':'orpi','AVendreALouer':'av','PAP':'pap','Notaires':'notaires','Properstar':'ps','Laforêt':'laf','Century 21':'c21','Logic-Immo':'li'}
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
def fuzzy(c,n):
    for j,x in enumerate(L):
        if x['c']!=c or abs(x['p']-n['p'])>1000:continue
        if n['a'] and x['a'] and abs(x['a']-n['a'])>3:continue
        if n['l'] and x['l'] and abs(x['l']-n['l'])>max(20,.1*x['l']):continue
        if not (n['a'] or n['l']):continue
        return j
def dist(c,q):
    if (c,q) in QD:return QD[(c,q)]+(1,)
    if c=='Nîmes':return ('inconnue','Quartier non précisé, distance à la gare inconnue',0)
    t=DRIVE.get(c,20);return ('voiture' if t<=15 else 'loin','Estimation: ≈ %d min en voiture de la gare de Nîmes'%t,1)
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

PFXU={"Bien'ici":'https://www.bienici.com/annonce/','Leboncoin':'https://www.leboncoin.fr/ad/ventes_immobilieres/'}
def load_delta(fn):
    raw=open(fn).read()
    if raw.lstrip().startswith('{') and '\n' not in raw.strip().split('\n')[0][:0] and raw.count('\n')<=1 and '"nw"' in raw:
        return json.loads(raw)
    head,*rows=raw.strip().split('\n');h=json.loads(head);src=h['src']
    d=dict(src=src,n=h['n'],seen=[],pp=h['pp'],up=h['up'],lk=[[i,l or src,(u if u.startswith('http') else PFXU[src]+u),p] for i,l,u,p in h['lk']],nw=[],skip=h.get('skip',0),errs=h.get('errs',[]))
    for r in rows:
        f=r.split('|')
        id_,url,c,p,a,l,ro,b,dpe,y,pub,mod,dec,q,fl=f
        flags={}
        for kv in fl.split(','):
            if kv:
                k,v=kv.split('=');flags[k]=int(v) if v.lstrip('-').isdigit() else v
        d['nw'].append(dict(s=src,id=id_,url=url or PFXU[src]+id_,c=c,p=int(p),a=int(a),l=int(l),r=int(ro),b=int(b),dpe=dpe,y=int(y),pub=pub,mod=mod,dec=int(dec),q=q,f=flags))
    return d
files=sorted(glob.glob(D('scan/runs/d_*')))
if not files and not os.path.exists(D('scan/runs/manual.json')):print('aucun delta à appliquer');sys.exit(0)
seen=set()
for fn in files:
    d=load_delta(fn);src=d['src']
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
        f=dict(ca=0,lg=0,g='?',pi='n',cl=0,mi='?',bu=0,pl=0,p2=0,tr='n',jd=0,vi=0,ms=0,ur=0,rx=0);f.update(n['f']);c=n['c'];k=PFX.get(n['s'],n['s'][:3].lower())+'-'+n['id'].replace('/','_').lstrip('_').replace('annonce_','')
        if any(x['k']==k for x in L):continue
        j=fuzzy(c,n)
        if j is not None:
            if not any(u[1]==n['url'] for u in L[j]['u']):L[j]['u'].append([n['s'],n['url'],n['p']]);log['liens ajoutés (doublon de nouvelle annonce)']+=1
            continue
        dc,dl,de=dist(c,n['q'])
        ex=exclusion(n,f)
        x=dict(k=k,c=c,q=n['q'],p=n['p'],o=0,a=n['a'],l=n['l'],r=n['r'],b=n['b'],be=0,dpe=n['dpe'],y=n['y'],g=f['g'],gm=0,cl=f['cl'],pi=f['pi'],ca=f['ca'],mi=f['mi'],bu=f['bu'],tr=f['tr'],pl=f['pl'],p2=f['p2'],pd=1 if n.get('dec') else 0,pa=0,pub=n['pub'] if n['pub']!='1970-01-01' else '',mod=n['mod'],dc=dc,dl=dl,de=de,u=[[n['s'],n['url'],n['p']]],grp='A' if c=='Nîmes' else 'B',st='',pm=0,vi=f['vi'],ms=f['ms'],jd=f['jd'],jt=0,te=0,tx=1,ex=ex,ur=f['ur'],lg=f['lg'],sd=TODAY)
        L.append(x);P['items'][k]=[[TODAY,n['p']]];log['nouvelles annonces']+=1
        notes.append(f"NOUVEAU {k} {c} {n['p']} € {n['a']} m²"+(f" [exclu: {ex}]" if ex else ''))
    for s in M['sources']:
        if s['n'].startswith(src.split(' ')[0]):s['st']='ok';s['d']=TODAY
    if not DRY:
        os.makedirs(D('scan/runs/done'),exist_ok=True);shutil.move(fn,D('scan/runs/done/'+TODAY+'_'+os.path.basename(fn)))
# --- annonces ajoutées à la main (Firebase veille/manual, récupérées par le navigateur dans scan/runs/manual.json) ---
mf=D('scan/runs/manual.json')
if os.path.exists(mf):
    for m in json.load(open(mf)):
        k=m['k']
        if any(x['k']==k for x in L):continue
        f=dict(ca=0,lg=0,g='?',pi='n',cl=0,mi='?',bu=0,pl=0,p2=0,tr='n',jd=0);f.update(m.get('f',{}))
        c=m['c'];dup=fuzzy(c,m)
        dc,dl,de=dist(c,m.get('q',''))
        pub=datetime.datetime.fromtimestamp(m.get('ts',0)/1000).date().isoformat() if m.get('ts') else TODAY
        x=dict(k=k,c=c,q=m.get('q',''),p=m['p'],o=0,a=m.get('a',0),l=m.get('l',0),r=m.get('r',0),b=m.get('b',0),be=0,dpe=m.get('dpe',''),y=0,g=f['g'],gm=0,cl=f['cl'],pi=f['pi'],ca=f['ca'],mi=f['mi'],bu=f['bu'],tr=f['tr'],pl=f['pl'],p2=f['p2'],pd=0,pa=0,pub=pub,mod=pub,dc=dc,dl=dl,de=de,u=[[m.get('src') or 'Ajout manuel',m['u'],m['p']]],grp='A' if c=='Nîmes' else 'B',st='',pm=0,vi=0,ms=0,jd=f['jd'],jt=0,te=0,tx=1,ex='',ur=0,lg=f['lg'],sd=TODAY,nt=m.get('nt',''),man=1,by=m.get('by',''))
        L.append(x);P['items'][k]=[[TODAY,m['p']]];log['annonces manuelles intégrées']+=1
        notes.append(f"MANUEL {k} ({m.get('by','?')}) {c} {m['p']} €"+(f" [doublon possible de {L[dup]['k']}]" if dup is not None else ''))
    if not DRY:
        os.makedirs(D('scan/runs/done'),exist_ok=True);shutil.move(mf,D('scan/runs/done/'+TODAY+'_manual.json'))
for i in seen:L[i]['sd']=TODAY
P['scan']=TODAY
if not DRY:
    json.dump(L,open(D('data/listings.json'),'w'),ensure_ascii=False,separators=(',',':'))
    json.dump(P,open(D('data/prices.json'),'w'),ensure_ascii=False,separators=(',',':'))
    json.dump(M,open(D('data/meta.json'),'w'),ensure_ascii=False,indent=1)
print(dict(log));print('\n'.join(notes))
print('total annonces:',len(L))
