# -*- coding: utf-8 -*-
# Drave Visual Buddy - de Buddy Browser (0.5): nu IN het Buddy-venster zelf.
# Buddy ziet de pagina zoals die gebouwd is en leest voor vanaf waar jij bent.
# 0.5: de gelezen alinea krijgt een los geel kader EROVERHEEN (de pagina zelf wordt niet meer aangepast).
# Klik-en-lees: klik op een alinea en Buddy leest vanaf daar. Buddy klikt zelf niets en verstuurt niets.
# Inloggen en cookies blijven in de map browserdata naast de app (op D:, niet op C:).
import os, sys, re

HERE = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "browserdata")
START = "https://www.google.nl"

BLOKKEN_JS = r"""
(function(){
  const SEL='h1,h2,h3,h4,h5,h6,p,li,blockquote,figcaption,dt,dd,td,th,pre,summary,label,caption';
  const weg=e=>e.closest('nav,aside,footer,script,style,noscript,[role=navigation],[role=contentinfo],[aria-hidden=true]');
  const lm=document.getElementById('__buddyLees');                 // 0.6: in de leesmodus alleen het artikel
  let els=lm?[...lm.querySelectorAll(SEL)]:[...document.querySelectorAll(SEL)].filter(e=>!weg(e));
  els=els.filter(e=>{const r=e.getBoundingClientRect(); const s=getComputedStyle(e);
                     return r.width>0&&r.height>0&&s.visibility!='hidden'&&s.display!='none';});
  const set=new Set(els);
  els=els.filter(e=>![...e.querySelectorAll(SEL)].some(c=>set.has(c)));
  els=els.filter(e=>(e.innerText||'').trim().length>1);
  window.__buddy=els;
  let start=0;
  for(let i=0;i<els.length;i++){const r=els[i].getBoundingClientRect(); if(r.bottom>40){start=i;break;}}
  const teksten=els.map(e=>(e.innerText||'').replace(/\s+/g,' ').trim());
  if(teksten.length<2){return {start:0, teksten:(document.body.innerText||'').split('\n').map(t=>t.trim()).filter(t=>t.length>1), markeer:false};}
  return {start:start, teksten:teksten, markeer:true};
})()
"""

# 0.5: een los kader (div) boven op de pagina, dat met het scrollen meebeweegt. Er is er altijd maar een.
MARKEER_JS = r"""
(function(i){
  const els=window.__buddy||[];
  let k=document.getElementById('__buddyKader');
  if(!k){
    k=document.createElement('div'); k.id='__buddyKader';
    k.style.cssText='position:fixed;pointer-events:none;z-index:2147483647;border:4px solid #ffd84d;'+
                    'background:rgba(255,230,80,0.28);border-radius:6px;display:none;box-sizing:border-box;';
    document.documentElement.appendChild(k);
    const zet=()=>{const el=window.__buddyEl; if(!el||!el.isConnected){k.style.display='none';return;}
      let r=el.getBoundingClientRect();
      try{const rg=document.createRange(); rg.selectNodeContents(el); const t=rg.getBoundingClientRect();
          if(t.width>0&&t.height>0){r={left:Math.min(r.left,t.left),top:Math.min(r.top,t.top),
                                       right:Math.max(r.right,t.right),bottom:Math.max(r.bottom,t.bottom)};}}catch(e){}
      k.style.left=(r.left-6)+'px'; k.style.top=(r.top-4)+'px';
      k.style.width=(r.right-r.left+12)+'px'; k.style.height=(r.bottom-r.top+8)+'px'; k.style.display='block';};
    window.__buddyZet=zet;
    window.addEventListener('scroll',()=>requestAnimationFrame(zet),true);
    window.addEventListener('resize',()=>requestAnimationFrame(zet));
  }
  if(i<0||i>=els.length){window.__buddyEl=null; k.style.display='none'; return;}
  const el=els[i]; window.__buddyEl=el;
  const r=el.getBoundingClientRect();
  if(r.top<60||r.bottom>window.innerHeight-20){el.scrollIntoView({block:'center'});}
  window.__buddyZet();
})(%d)
"""

KLIK_JS = r"""
(function(aan){
  window.__buddyKlik=aan;
  if(!window.__buddyKlikGezet){
    window.__buddyKlikGezet=true;
    document.addEventListener('click',function(e){
      if(!window.__buddyKlik) return;
      e.preventDefault(); e.stopPropagation();
      console.log('BUDDYKLIK');
      window.__buddyDoel=e.target;
    },true);
  }
  document.body.style.cursor=aan?'help':'';
})(%s)
"""

INDEX_VAN_DOEL_JS = r"""
(function(){
  const els=window.__buddy||[]; let d=window.__buddyDoel;
  while(d){const i=els.indexOf(d); if(i>=0) return i; d=d.parentElement;}
  if(window.__buddyDoel){const r=window.__buddyDoel.getBoundingClientRect();
    for(let i=0;i<els.length;i++){if(els[i].getBoundingClientRect().bottom>=r.top) return i;}}
  return -1;
})()
"""

# 0.6: LEESMODUS - alleen het artikel, groot en rustig, over de pagina heen. Nog een keer = weer weg.
LEESMODUS_JS = r"""
(function(aan){
  let lm=document.getElementById('__buddyLees');
  if(lm){lm.remove(); document.documentElement.style.overflow=window.__buddyOverflow||''; }
  if(!aan) return 0;
  // 0.6.1: elk blokje met lopende tekst telt mee (niet alleen <p>), zoals de leesmodus van gewone browsers.
  const weg=e=>e.closest('nav,aside,footer,figure,script,style,noscript,button,select,svg,iframe,[role=navigation],[role=complementary],[role=contentinfo],[aria-hidden=true],[hidden]');
  const INLINE=new Set(['A','B','I','EM','STRONG','SPAN','SMALL','SUB','SUP','BR','MARK','U','S','ABBR','CITE','Q','CODE','TIME','FONT','LABEL','WBR']);
  const schoon=t=>(t||'').replace(/\s+/g,' ').trim();
  const zicht=e=>{const s=getComputedStyle(e); return s.display!='none'&&s.visibility!='hidden';};
  const isBlok=e=>{const d=getComputedStyle(e).display; return !d.startsWith('inline')||/^H[1-6]$/.test(e.tagName);};
  // eigen tekst van een blokje: losse tekst + tekst in schuine/vette/link-stukjes, NIET de tekst van blokjes erin
  const eigen=e=>{let t='', links=0;
    for(const c of e.childNodes){
      if(c.nodeType==3) t+=c.textContent;
      else if(c.nodeType==1&&(INLINE.has(c.tagName)||!isBlok(c))&&!weg(c)){const x=c.innerText||''; t+=' '+x+' '; if(c.tagName=='A') links+=schoon(x).length;}
    }
    t=schoon(t).replace(/\s+([,.;:!?)\]])/g,'$1').replace(/([(\[])\s+/g,'$1'); return {t:t, links:links};};
  const alle=[...document.body.querySelectorAll('*')].filter(e=>!INLINE.has(e.tagName)&&!weg(e)&&zicht(e)&&isBlok(e));
  // 1. waar staat het artikel? de plek met de meeste lopende tekst (weinig links)
  const score=new Map();
  for(const e of alle){
    const {t,links}=eigen(e); const n=t.length;
    if(n<40||links>n*0.5) continue;
    let a=e.parentElement, f=1;
    for(let k=0;k<3&&a;k++,a=a.parentElement,f/=2){score.set(a,(score.get(a)||0)+n*f);}
  }
  let wortel=null, best=0;
  for(const [e,v] of score){ if(v>best){best=v; wortel=e;} }
  if(!wortel||best<200) return 0;
  const art=wortel.closest('article,[role=main],main');
  if(art&&art!==document.body){const extra=[...art.querySelectorAll('*')].length; if(extra<4000) wortel=art;}
  // 2. de stukjes tekst in volgorde
  let stukken=[];
  for(const e of wortel.querySelectorAll('*')){
    if(INLINE.has(e.tagName)||weg(e)||!zicht(e)||!isBlok(e)) continue;
    const kop=/^H[1-4]$/.test(e.tagName);
    const {t,links}=kop?{t:schoon(e.innerText),links:0}:eigen(e);
    if(t.length<2) continue;
    if(!kop&&links>t.length*0.6&&t.length<120) continue;           // lijstjes met alleen links overslaan
    stukken.push({tag:kop?e.tagName.toLowerCase():(e.tagName=='LI'?'li':(e.tagName=='BLOCKQUOTE'?'blockquote':'p')), t:t});
  }
  const h1=[...document.querySelectorAll('h1')].find(h=>schoon(h.innerText).length>3);       // de echte titel (niet het logo)
  if(h1&&!stukken.some(x=>x.t==schoon(h1.innerText))) stukken.unshift({tag:'h1', t:schoon(h1.innerText)});
  if(stukken.length<3) return 0;
  // 3. het leesvel
  lm=document.createElement('div'); lm.id='__buddyLees';
  lm.style.cssText='all:initial;position:fixed;inset:0;z-index:2147483646;overflow-y:auto;overflow-x:hidden;background:#16131f;display:block;';
  const vel=document.createElement('div');
  vel.style.cssText='all:initial;display:block;max-width:900px;margin:0 auto;padding:40px 48px 120px;'+
                    'font-family:Segoe UI,Arial,sans-serif;color:#f0f0f5;font-size:26px;line-height:1.65;';
  const bron=document.createElement('div'); bron.textContent=location.hostname.replace(/^www\./,'')+'  -  Leesmodus';
  bron.style.cssText='all:initial;display:block;font-family:Segoe UI,Arial,sans-serif;font-size:18px;color:#9696aa;margin-bottom:24px;';
  vel.appendChild(bron);
  for(const s of stukken){
    const kop=/^h[1-4]$/.test(s.tag);
    const n=document.createElement(kop?s.tag:(s.tag=='blockquote'?'blockquote':'p'));
    n.textContent=(s.tag=='li'?'•  ':'')+s.t;
    const grootte={h1:'44px',h2:'34px',h3:'30px',h4:'28px'}[s.tag]||'26px';
    n.style.cssText='all:initial;display:block;font-family:Segoe UI,Arial,sans-serif;font-size:'+grootte+';line-height:1.55;'+
                    'color:'+(kop?'#b59cff':'#f0f0f5')+';font-weight:'+(kop?'700':'400')+';margin:'+(kop?'34px 0 16px':'0 0 22px')+';'+
                    (s.tag=='blockquote'?'border-left:5px solid #7F77DD;padding-left:20px;font-style:italic;':'');
    vel.appendChild(n);
  }
  lm.appendChild(vel); document.documentElement.appendChild(lm);
  window.__buddyOverflow=document.documentElement.style.overflow; document.documentElement.style.overflow='hidden';
  return stukken.length;
})(%s)
"""

# "Wat staat er?" voor de Buddy Browser: zelfde soort overzicht als bij andere vensters
OVERZICHT_JS = r"""
(function(){
  const zicht=e=>{const r=e.getBoundingClientRect(); return r.width>0&&r.height>0&&r.bottom>0&&r.top<window.innerHeight;};
  const t=e=>(e.innerText||e.value||e.getAttribute('aria-label')||e.getAttribute('placeholder')||e.title||'').replace(/\s+/g,' ').trim();
  const q=s=>[...document.querySelectorAll(s)].filter(zicht);
  const koppen=q('h1,h2,h3').map(t).filter(x=>x).slice(0,6);
  const knoppen=q('button,[role=button],input[type=submit],input[type=button]').map(t).filter(x=>x&&x.length<40).slice(0,8);
  const velden=q('input[type=text],input[type=search],input[type=email],input:not([type]),textarea').map(t).filter(x=>x).slice(0,5);
  const links=q('a[href]'); const ln=links.map(t).filter(x=>x&&x.length<60).slice(0,6);
  return {titel:document.title||'', koppen:koppen, knoppen:knoppen, velden:velden, links:links.length, linknamen:ln};
})()
"""


# 0.9: de geopende mail uitlezen (Gmail eerst, andere webmail zo goed als het gaat). Leest alleen, verandert niets.
MAIL_JS = r"""
(function(){
  function zichtbaar(e){ var r=e.getBoundingClientRect(); return r.width>0 && r.height>0; }
  var uit={afzender:'', naam:'', onderwerp:'', tekst:'', links:[], bron:''};
  var bodies=[].slice.call(document.querySelectorAll('div.a3s')).filter(zichtbaar);
  if(bodies.length){                                   // Gmail
    uit.bron='gmail';
    var body=bodies[bodies.length-1];
    var s=document.querySelector('h2.hP'); if(s) uit.onderwerp=s.innerText.trim();
    var afz=[].slice.call(document.querySelectorAll('span.gD')).filter(zichtbaar);
    if(afz.length){ var a=afz[afz.length-1]; uit.afzender=a.getAttribute('email')||''; uit.naam=a.getAttribute('name')||a.innerText||''; }
    uit.tekst=body.innerText.trim();
    [].forEach.call(body.querySelectorAll('a[href]'), function(l){ uit.links.push({tekst:(l.innerText||'').trim().slice(0,200), href:l.href}); });
    return uit;
  }
  var sel=window.getSelection().toString().trim();      // andere webmail: selectie, of het hoofdstuk van de pagina
  var hoofd=document.querySelector('[role=main]')||document.querySelector('main')||document.body;
  uit.bron=sel?'selectie':'pagina';
  uit.onderwerp=document.title||'';
  uit.tekst=(sel||hoofd.innerText||'').trim().slice(0,20000);
  var m=uit.tekst.match(/[\w.+-]+@[\w-]+(\.[\w-]+)+/); if(m) uit.afzender=m[0];
  [].forEach.call(hoofd.querySelectorAll('a[href]'), function(l){ if(zichtbaar(l)) uit.links.push({tekst:(l.innerText||'').trim().slice(0,200), href:l.href}); });
  uit.links=uit.links.slice(0,300);
  return uit;
})()
"""

# 0.9: verdachte links in de pagina dik rood omlijnen (%s = JSON-lijst met domeinen)
ROOD_JS = r"""
(function(lijst){
  var n=0;
  [].forEach.call(document.querySelectorAll('a[href]'), function(l){
    var h=(l.hostname||'').toLowerCase().replace(/^www\./,'');
    if(lijst.some(function(d){ return h===d || h.slice(-d.length-1)==='.'+d; })){
      l.style.outline='5px solid #ff3030'; l.style.outlineOffset='2px'; l.style.background='#ffe0e0';
      l.title='PAS OP: verdachte link (Drave Visual Buddy)'; n++;
    }
  });
  return n;
})(%s)
"""


def adres_naar_url(t):
    """Wat pa in het adresvak typt: een adres of gewoon een zoekwoord."""
    from PyQt6.QtCore import QUrl
    t = (t or "").strip()
    if not t:
        return None
    if " " in t or "." not in t:
        return QUrl("https://www.google.nl/search?q=" + QUrl.toPercentEncoding(t).data().decode())
    return QUrl(t if re.match(r"^\w+://", t) else "https://" + t)


def maak_profiel(app):
    from PyQt6.QtWebEngineCore import QWebEngineProfile
    os.makedirs(DATA, exist_ok=True)
    profiel = QWebEngineProfile("buddy", app)                   # eigen, blijvend profiel (inloggen onthouden)
    profiel.setPersistentStoragePath(DATA)
    profiel.setCachePath(os.path.join(DATA, "cache"))
    profiel.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
    return profiel
