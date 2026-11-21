/* Bibliothèque de relève (à exécuter DANS la page d'un site via le navigateur intégré).
   Chargement:  eval(await (await fetch('https://raw.githubusercontent.com/math-lrx/veille-maison/main/scan/lib.js')).text())
   (si la politique de sécurité du site l'interdit, coller le fichier tel quel dans l'outil javascript). */
(function(){
const PAGES='https://math-lrx.github.io/veille-maison/';
const CITIES={'nimes':'Nîmes','caissargues':'Caissargues','bouillargues':'Bouillargues','redessan':'Redessan','rodilhan':'Rodilhan','garons':'Garons','manduel':'Manduel','bellegarde':'Bellegarde','generac':'Générac'};
const norm=s=>String(s||'').normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase().replace(/[^a-z]/g,'');
const cityOf=s=>{const n=norm(s);for(const k in CITIES)if(n.startsWith(k))return CITIES[k];return null};
const RC=/(?<![a-zà-ÿ])(caves?|caveau|sous[- ]?sols?|semi[- ]?enterr[ée]e?s?)(?![a-zà-ÿ])/i;
const RD=[/(deux|2)\s+(logements?|appartements?|habitations?|maisons?\s+(ind|dist|s[ée]par))/i,/(logement|appartement|studio|t1|t2|f1|f2|gîte|gite)\s+(totalement\s+|enti[èe]rement\s+)?(ind[ée]pendant|attenant|annexe|s[ée]par[ée]|am[ée]nag[ée]|en\s+rez)/i,/\bstudio\b/i,/\b(gîte|gite)s?\b/i,/(rez[- ]de[- ]chauss[ée]e|rdc)\s+et\s+(l['’]\s*)?[ée]tage\s+(sont\s+|est\s+)?ind[ée]pendants?/i,/(deux|2)\s+entr[ée]es\s+ind[ée]pendantes?/i,/entr[ée]e\s+ind[ée]pendante/i,/(second|deuxi[èe]me|2[èe]?me|2nd)\s+logement/i,/logement\s+(annexe|d['’]amis|de\s+fonction|locatif)|maison\s+d['’]amis|appartement\s+d['’]amis/i,/(d[ée]pendance|annexe|pool[- ]?house)\s+(am[ée]nag[ée]e?|habitable|transform[ée]e?)/i,/plusieurs\s+logements|deux\s+habitations|double\s+habitation|duplex\s+ind[ée]pendant/i];
const POT=/possibilit|pourr|peut|peuvent|permett|envisag|cr[ée]er|cr[ée]ation|potentiel|projet|selon|id[ée]al pour|ais[ée]ment|transform|am[ée]nager en|divis/i;
function classify(t,o){o=o||{};t=String(t||'');const f={};
 f.ca=RC.test(t)?1:0;
 let lg=0;for(const r of RD){const m=t.match(r);if(m){const ctx=t.slice(Math.max(0,m.index-80),m.index+m[0].length+80);lg=Math.max(lg,POT.test(ctx)?1:2)}}f.lg=lg;
 f.g=/(sans|pas de|aucun)\s+garage/i.test(t)?'?':(/garage|box\s+ferm/i.test(t)||o.garage)?'o':'?';
 f.pi=(o.pool||/piscine/i.test(t))?((/(possibilit[ée]|projet|emplacement|pr[ée]vu|installer|construire|cr[ée]er)[^.]{0,50}piscine|piscine[^.]{0,40}(possible|envisageable|[àa] construire|en projet)/i.test(t)&&!o.pool)?'p':'o'):'n';
 f.cl=(o.clim||/climatisation|climatis[ée]|\bclim\b|r[ée]versible/i.test(t))?1:0;
 f.mi=/(non|pas|sans|aucune?)[ -]+(de\s+)?mitoyen|ind[ée]pendante?\b|4 fa[çc]ades|quatre fa[çc]ades|aucun vis[- ]?[àa][- ]?vis/i.test(t)?'n':/mitoyen|jumel/i.test(t)?'o':'?';
 f.bu=/bureau/i.test(t)?1:0;f.pl=/plain[- ]?pied/i.test(t)?1:0;
 f.p2=/(deux|2|plusieurs|double)\s+(places?\s+de\s+(parking|stationnement)|garages?|parkings?|v[ée]hicules?)|double garage|garage double/i.test(t)?1:0;
 f.tr=(o.work||(/travaux|r[ée]nover|r[ée]novation|rafra[iî]chir|remise au go[uû]t|[àa] r[ée]habiliter/i.test(t)&&!/(aucun|sans|pas de)\s+travaux/i.test(t)))?'l':'n';
 f.jd=/jardin|terrain\s+(clos|arbor|plat)|parcelle|pelouse/i.test(t)||o.garden?1:0;
 f.rx=/(r[ée]novation|travaux)\s+(importants?|complets?|compl[èe]te|lourds?)|enti[èe]rement\s+[àa]\s+r[ée]nover|[àa]\s+r[ée]nover\s+enti[èe]rement|gros\s+travaux|[àa]\s+r[ée]habiliter|int[ée]gralement\s+[àa]\s+r[ée]nover|enti[èe]rement\s+[àa]\s+r[ée]nov/i.test(t)?1:0;
 f.vi=/viager|nue[- ]propri[ée]t[ée]/i.test(t)?1:0;
 f.ms=/\bpermis de construire\b[^.]{0,40}(non|sans)|terrain\s+[àa]\s+b[âa]tir|projet de construction|maison [àa] construire|vente en l['’]?[ée]tat futur|VEFA/i.test(t)?1:0;
 f.ur=/maison de (ville|village)|village house|centre[- ]ville|centre[- ]village|ruelle/i.test(t)?1:0;
 return f}
const canon=u=>{u=String(u||'').replace(/^https?:\/\/(www\.)?/i,'').replace(/[?#].*$/,'').replace(/\/$/,'').toLowerCase();return u};
const num=s=>{const m=String(s||'').replace(/[\s  ]/g,'').match(/\d+/);return m?+m[0]:0};
const pid=u=>{const c=canon(u);let m=c.match(/bienici\.com\/annonce\/(.+)$/);if(m)return 'bi:'+m[1];m=c.match(/leboncoin\.fr\/(?:ad\/[a-z_]+\/)?(\d+)/);if(m)return 'lbc:'+m[1];m=c.match(/seloger\.com\/annonces?\/.*\/([0-9a-z]{8,})$/);if(m)return 'sl:'+m[1];m=c.match(/fd-(\d+)$/);if(m)return 'av:'+m[1];return c};
async function load(){if(window.VH_L)return window.VH_L;const L=await (await fetch(PAGES+'data/listings.json?v='+Date.now())).json();const known={};L.forEach((x,i)=>x.u.forEach(u=>{known[pid(u[1])]=i}));window.VH_L=L;window.VH_K=known;return L}
function fuzzy(L,r){for(let i=0;i<L.length;i++){const x=L[i];if(norm(x.c)!==norm(r.c))continue;const d=Math.abs(x.p-r.p);if(d>1000)continue;if(r.a&&x.a&&Math.abs(x.a-r.a)>3)continue;if(r.l&&x.l&&Math.abs(x.l-r.l)>Math.max(20,.1*x.l))continue;if(!r.a&&!r.l)continue;return i}return -1}
/* recs: [{id,url,c,p,a,l,r,b,t,d,pub,mod,pool,clim,garden,work,dpe,y,dec}]  -> delta compact */
async function delta(recs,label){const L=await load(),K=window.VH_K;const out={src:label,n:recs.length,seen:[],pp:[],up:[],lk:[],nw:[],skip:0};
 for(const r of recs){r.p=Array.isArray(r.p)?Math.min(...r.p.map(Number).filter(Boolean)):Number(r.p)||0;const c=cityOf(r.c);if(!c){out.skip++;continue}r.c=c;
  const f=classify((r.t||'')+' . '+(r.d||''),r);let i=K[pid(r.url)];
  if(i===undefined&&r.p&&r.p<=400000){i=fuzzy(L,r);if(i>=0){out.lk.push([i,label,r.url,r.p]);K[pid(r.url)]=i}}
  if(i!==undefined&&i>=0){out.seen.push(i);const x=L[i];const lkx=x.u.find(u=>pid(u[1])===pid(r.url));if(r.p&&lkx&&lkx[2]!==r.p)out.pp.push([i,r.url,r.p,lkx[2]||0]);
    const up={};if(f.ca&&!x.ca)up.ca=1;if(f.lg>(x.lg||0))up.lg=f.lg;if(f.vi)up.vi=1;if(Object.keys(up).length)out.up.push([i,up]);continue}
  if(!r.p||r.p>400000){out.skip++;continue}
  if((r.a&&r.a<90)||(r.b&&r.b<3))continue;
  out.nw.push({s:label,id:r.id,url:r.url,c:r.c,p:r.p,a:r.a||0,l:r.l||0,r:r.r||0,b:r.b||0,dpe:r.dpe||'',y:r.y||0,pub:r.pub||'',mod:r.mod||'',dec:r.dec?1:0,q:(r.q||'').slice(0,40),f:Object.fromEntries(Object.entries(f).filter(([k,v])=>v&&v!=='?'&&v!=='n'))})}
 out.seen=[...new Set(out.seen)];return out}

const PRICE=/(\d{1,3}(?:[ \u00a0\u202f.]\d{3})+|\d{5,7})\s*€/;
const AREA=/(\d{2,4}(?:[.,]\d)?)\s*m(?:²|2)(?!\s*(?:de\s+)?(?:terrain|jardin|parcelle))/i;
function parse(t){t=String(t||'').replace(/[\s\u00a0\u202f]+/g,' ');const o={};let m=t.match(PRICE);o.p=m?num(m[1].replace(/\./g,'')):0;
 m=t.match(AREA);o.a=m?Math.round(parseFloat(m[1].replace(',','.'))):0;
 m=t.match(/(\d+)\s*pi[èe]ces?/i);o.r=m?+m[1]:0;m=t.match(/(\d+)\s*chambres?/i);o.b=m?+m[1]:0;
 m=t.match(/(?:terrain|parcelle|jardin)[^\d]{0,25}(\d[\d ]{1,6})\s*m(?:²|2)/i)||t.match(/(\d[\d ]{1,6})\s*m(?:²|2)\s*(?:de\s+)?(?:terrain|jardin|parcelle)/i);o.l=m?num(m[1]):0;return o}
/* cfg: {name, base?, urls:[ 'https://.../liste?p={p}' ... ] (ou chemins relatifs), pages:N, linkRe: RegExp, city?:(url,text)=>nom, detail?:true, max?:40} */
async function htmlSource(cfg){const L=await load(),K=window.VH_K;const seenUrl=new Set(),cand=[];
 for(const tpl of cfg.urls){for(let p=cfg.p0===undefined?1:cfg.p0;p<(cfg.p0===undefined?1:cfg.p0)+(cfg.pages||1);p++){let html;try{const r=await fetch(tpl.replace('{p}',p));if(!r.ok){cand.push({err:r.status+' '+tpl});break}html=await r.text()}catch(e){cand.push({err:'ERR '+tpl});break}
  const d=new DOMParser().parseFromString(html,'text/html');let n=0;
  d.querySelectorAll('a[href]').forEach(a=>{let h=a.getAttribute('href');if(!cfg.linkRe.test(h))return;const url=new URL(h,tpl.startsWith('http')?tpl:location.origin+tpl).href.replace(/[?#].*$/,'');if(seenUrl.has(url))return;seenUrl.add(url);n++;
   let c=a;for(let k=0;k<6&&c.parentElement;k++){c=c.parentElement;if(PRICE.test(c.innerText||''))break}const text=(c.innerText||a.innerText||'').replace(/\s+/g,' ').slice(0,400);cand.push({url,text,t:text})});
  if(!n)break}}
 const errs=cand.filter(x=>x.err).map(x=>x.err);const recs=[];
 for(const x of cand){if(x.err)continue;const o=parse(x.text);const r={id:x.url.replace(/^https?:\/\/[^/]+/,'').replace(/[^A-Za-z0-9]+/g,'_').slice(-40),url:x.url,c:(cfg.city?cfg.city(x.url,x.text):x.text)||'',p:o.p,a:o.a,l:o.l,r:o.r,b:o.b,t:x.text,d:''};recs.push(r)}
 /* détail pour les candidats inconnus */
 let det=0;for(const r of recs){const c=cityOf(r.c)||cityOf(r.t)||cityOf(r.url);if(c)r.c=c;if(!r.p||r.p>400000||!cityOf(r.c))continue;if(K[pid(r.url)]!==undefined)continue;if(fuzzy(L,r)>=0)continue;if(cfg.detail===false||det>=(cfg.max||40))continue;det++;
  try{const h=await (await fetch(r.url)).text();const dd=new DOMParser().parseFromString(h,'text/html');dd.querySelectorAll('script,style,nav,footer,header').forEach(e=>e.remove());const s=dd.body.innerText.replace(/[\s\u00a0]+/g,' ');const o=parse(s);r.d=s.slice(0,6000);if(!r.a)r.a=o.a;if(!r.l)r.l=o.l;if(!r.b)r.b=o.b;if(!r.r)r.r=o.r}catch(e){}}
 const out=await delta(recs,cfg.name);out.errs=errs;out.found=recs.length;return out}

async function leboncoin(){const L=await load(),K=window.VH_K;const cps=['30000','30900','30132','30230','30129','30128','30127','30510'];const recs=[],errs=[];
 for(const cp of cps){for(let p=1;p<=20;p++){let j;try{const r=await fetch('/cl/ventes_immobilieres/cp_x_'+cp+'/real_estate_type:1/price:0-400000/square:90-max?page='+p);if(!r.ok){errs.push(r.status+' '+cp);break}const h=await r.text();j=JSON.parse(h.match(/<script id="__NEXT_DATA__"[^>]*>(.*?)<\/script>/s)[1]).props.pageProps.searchData}catch(e){errs.push('ERR '+cp+' '+p);break}
  const ads=j.ads||[];ads.forEach(a=>{const at={};(a.attributes||[]).forEach(x=>at[x.key]=x.value);recs.push({id:String(a.list_id),url:'https://www.leboncoin.fr/ad/ventes_immobilieres/'+a.list_id,c:a.location&&a.location.city,p:a.price&&a.price[0],a:+at.square||0,l:+at.land_plot_surface||0,r:+at.rooms||0,b:0,t:a.subject,d:'',pub:(a.first_publication_date||'').slice(0,10),mod:(a.index_date||'').slice(0,10),dpe:(at.energy_rate||'').toUpperCase(),y:+at.building_year||0,pa:a.owner&&a.owner.type==='private'})});
  if(p>=(j.max_pages||1)||!ads.length)break}}
 const uniq=new Map();recs.forEach(r=>uniq.set(r.id,r));const R=[...uniq.values()];let det=0;
 for(const r of R){const c=cityOf(r.c);if(!c)continue;r.c=c;if(!r.p||r.p>400000)continue;if(K[pid(r.url)]!==undefined||fuzzy(L,r)>=0)continue;if(det++>=40)continue;
  try{const h=await (await fetch('/ad/ventes_immobilieres/'+r.id)).text();const ad=JSON.parse(h.match(/<script id="__NEXT_DATA__"[^>]*>(.*?)<\/script>/s)[1]).props.pageProps.ad;r.d=String(ad.body||'').slice(0,6000)}catch(e){}}
 const out=await delta(R,'Leboncoin');out.errs=errs;out.found=R.length;return out}
async function bienici(){const Z=[-378685,-378869,-379281,-379895,-378879,-382564,-379898,-384073,-382567];const all=[];
 for(let from=0;from<1000;from+=100){const f={size:100,from,showAllModels:false,filterType:'buy',propertyType:['house'],maxPrice:400000,minArea:90,page:from/100+1,sortBy:'relevance',sortOrder:'desc',onTheMarket:[true],zoneIdsByTypes:{zoneIds:Z}};
  const j=await (await fetch('/realEstateAds.json?filters='+encodeURIComponent(JSON.stringify(f)))).json();const ads=j.realEstateAds||[];all.push(...ads);if(from+100>=j.total||!ads.length)break}
 return all.map(a=>({id:a.id,url:'https://www.bienici.com/annonce/'+a.id,c:a.city,p:a.price,a:Math.round(a.surfaceArea||0),l:Math.round(a.landSurfaceArea||0),r:a.roomsQuantity||0,b:a.bedroomsQuantity||0,t:a.title,d:String(a.description||'').replace(/<br\s*\/?>/gi,' '),pub:(a.publicationDate||'').slice(0,10),mod:(a.modificationDate||'').slice(0,10),pool:a.hasPool,clim:a.hasAirConditioning,garden:a.hasGarden,work:a.workToDo,dpe:a.energyClassification||'',y:a.yearOfConstruction||0,dec:a.priceHasDecreased,q:a.district&&a.district.libelle||''}))}
window.VH={PAGES,CITIES,cityOf,classify,canon,pid,load,delta,bienici,htmlSource,leboncoin,parse,num,norm};
return 'VH prêt'})();
