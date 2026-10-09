// Moved from index.html (snapshot d689e08), line 2321; comments on calculations and sources added 2026-10-07; code unchanged.
// How they talked (from the "How They Talked" artifact). Wrapped in its own function so its names stay out of the page's.
(() => {
const NS="http://www.w3.org/2000/svg",el=(t,a,p)=>{const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);p&&p.appendChild(e);return e},tx=(p,a,s)=>{const e=el("text",a,p);e.textContent=s;return e};
/* DATA · C: one entry per city, built from the data files (no numbers typed in):
     pm, name, st (state), dates, rise, bad (= bad_days), ratio   from data/pm25.js (scripts/site/05_pm25.py; how each is made: js/plates-shared.js)
     read  Claude draft label counts per group, air = worst-week air items before sampling, X included
           (data/tone-counts.js, draft_read and air_items; scripts/site/02_tone_counts.py)
     big   Bakersfield only: draft counts in its biggest thread (tone-counts.js big_thread), for "leave out the biggest thread"
     fn    footnote numbers shown beside the city name (text, not data)
   C_ORDER is the order the cities are listed in and ties are broken by; kept as published. */
const C_ORDER=["bakersfield","fairbanks","fresno","detroit","indianapolis","seattle","eugene","sanjose","pittsburgh"];
const C_FN={bakersfield:"3",fairbanks:"2",detroit:"4",seattle:"1",eugene:"1,5",sanjose:"5",pittsburgh:"1,4"};
const C=Object.fromEntries(C_ORDER.map(k=>{const p=window.PM25.cities.find(c=>c.slug===k),T=window.TONE;
 const o={pm:p.pm,name:p.name,st:p.state,dates:p.dates,rise:p.rise,bad:p.bad_days,ratio:p.ratio,air:T.air_items[k],read:T.draft_read[k]};
 if(k==="bakersfield")o.big=T.big_thread[k];
 if(C_FN[k])o.fn=C_FN[k];
 return[k,o]}));
/* sort orders. Shares and peaks follow the current data (they change with "leave out Bakersfield's big thread") */
const PAIRS=["fairbanks","detroit","eugene","bakersfield","indianapolis","sanjose","fresno","pittsburgh","seattle"];   /* matched pairs, then the unpaired and crossed-pair cities */
/* THE TONE AXIS used by every chart in this file: 0 to 4, one unit per group, Alarm [0,1), Adjusting [1,2), Enduring [2,3),
   Normalizing [3,4]. Group b (0..3) sits at the centre of its unit, b + 0.5. Reacting = Alarm + Adjusting, living with it = Enduring + Normalizing.
   CALCULATION · shares(): share of group b = count_b / (count_A + count_J + count_E + count_N). "Not about the air" (X) is never counted. */
function shares(slug){const n=bandCounts(slug),t=n.reduce((a,b)=>a+b,0);return{n,t,sh:n.map(x=>x/t)}}
/* CALCULATION · peak = the point u on the 0-4 axis (checked every 0.025) where the smoothed curve kde(sh, u) is highest */
function peakOf(sh){let b=0;for(let k=0;k<=160;k++){const u=k/40;if(kde(sh,u)>kde(sh,b))b=u}return b}
/* CALCULATION · sort orders: by rise, PM2.5, ratio, alarm share, reacting share (A+J), living share (E+N), peak (leftmost first), comment count; ties go to more bad-air days */
function order(){const K=Object.keys(C),S=Object.fromEntries(K.map(k=>[k,shares(k)])),by=f=>K.slice().sort((a,b)=>f(b)-f(a)||C[b].bad-C[a].bad);
 switch(st.ord){
  case"rise":return by(k=>C[k].rise);
  case"pm":return by(k=>C[k].pm);
  case"ratio":return by(k=>C[k].ratio);
  case"alarm":return by(k=>S[k].sh[0]);
  case"react":return by(k=>S[k].sh[0]+S[k].sh[1]);
  case"living":return by(k=>S[k].sh[2]+S[k].sh[3]);
  case"peak":return by(k=>-peakOf(S[k].sh));
  case"n":return by(k=>S[k].t);
  case"az":return K.slice().sort((a,b)=>C[a].name.localeCompare(C[b].name));
  case"pairs":return PAIRS;
  default:return K.slice().sort((a,b)=>C[b].bad-C[a].bad||C[b].rise-C[a].rise)}}
function tagFor(slug){const s=C[slug],S=shares(slug),pc=x=>Math.round(x*100)+"%";
 switch(st.ord){
  case"pairs":return PAIRNOTE[slug];
  case"rise":case"ratio":return `Worst week ${s.ratio.toFixed(1)}× its normal PM2.5`;
  case"pm":return `Worst week ${s.pm.toFixed(0)} µg/m³ PM2.5`;
  case"alarm":return `${pc(S.sh[0])} alarm`;
  case"react":return `${pc(S.sh[0]+S.sh[1])} reacting`;
  case"living":return `${pc(S.sh[2]+S.sh[3])} living with it`;
  case"peak":{const p=peakOf(S.sh);return `Peaks in ${TG.four[Math.min(3,Math.floor(p))][0].toLowerCase()}`}
  case"n":return `${S.t} air comments`;
  default:return `${s.bad} unhealthy day${s.bad===1?"":"s"} a year`}}
const PAIRNOTE={fairbanks:"Matched pair 1 · more bad-air days",detroit:"Matched pair 1 · fewer bad-air days",bakersfield:"Matched pair 2 · more bad-air days",indianapolis:"Matched pair 2 · fewer bad-air days",fresno:"Matched pair 3 · more bad-air days",pittsburgh:"Matched pair 3 · fewer bad-air days",eugene:"Not in a pair",sanjose:"Crossed pairs only",seattle:"Crossed pairs only"};
const TG={
 two:[["Reacting","AJ","--t-alarm","Alarm + Adjusting"],["Living with it","EN","--t-endure","Enduring + Normalizing"]],
 three:[["Alarm","A","--t-alarm"],["Adjusting","J","--t-adjust"],["Living with it","EN","--t-endure","Enduring + Normalizing"]],
 four:[["Alarm","A","--t-alarm"],["Adjusting","J","--t-adjust"],["Enduring","E","--t-endure"],["Normalizing","N","--t-norm"]],
};
const SPOKES={two:[180,0],three:[-120,120,0],four:[-135,135,45,-45]};
/* texture and atmosphere are remembered per view, so the disks and the curves each keep their own look */
const VIEWST={disk:{grain:true,blur:false,ht:true,flare:false,link:false,rays:false},
 dens:{grain:false,blur:false,ht:false,flare:false,link:false,rays:false},
 time:{grain:false,blur:false,ht:false,flare:false,link:false,rays:false},
 quad:{grain:false,blur:false,ht:true,flare:true,link:false,rays:false},
 quotes:{grain:false,blur:false,ht:false,flare:false,link:false,rays:false},
 words:{grain:false,blur:false,ht:false,flare:false,link:false,rays:false},
 cloud:{grain:false,blur:false,ht:false,flare:false,link:false,rays:false}};
const st={qcity:"all",wcat:"all",ccat:"all",ccity:"all",ccol:"tone",wlay:"cloud",wmode:"freq",qflag:true,src:"claude",qcol:"tone",qname:true,qglow:false,qmove:true,rays:false,link:false,ht:false,flare:false,dot:"peak",pal:"riso",grain:false,blur:false,view:"dens",den:"gcurve",dn:"real",size:false,pctl:true,avg:true,grp:"four",ord:"bad",sc:"lin",col:"pal",lab:true,pct:true,base:false,tint:false,spk:true,cont:false,fill:false,big:false};
const FIX={"s-n": 0.25, "s-op": 55, "s-w": 0.6, "s-sp": 1, "s-tw": 14, "s-dr": 14, "s-pi": 0.42, "s-st": 1.3, "q-dr": 0.3, "q-tr": 0.5, "q-spd": 0.5, "w-n": 11, "w-sz": 1, "c-n": 150, "c-sz": 1, "q-sp": 1.6, "q-gap": 120};
const v=id=>FIX[id],pt=(c,r,a)=>[c+r*Math.cos(a),c+r*Math.sin(a)];
const css=n=>getComputedStyle(document.querySelector(".ht")||document.documentElement).getPropertyValue(n).trim();   // read from the wrapper: its tone colours live there
function blob(c,rs,an,pinch){const P=[],n=rs.length;for(let i=0;i<n;i++){const j=(i+1)%n,am=an[i]+((an[j]-an[i]+4*Math.PI)%(2*Math.PI))/2;P.push(pt(c,rs[i],an[i]));P.push(pt(c,Math.min(rs[i],rs[j])*pinch+5,am))}
 const m=P.length;let d=`M${P[0][0].toFixed(1)},${P[0][1].toFixed(1)}`;for(let i=0;i<m;i++){const p0=P[(i-1+m)%m],p1=P[i],p2=P[(i+1)%m],p3=P[(i+2)%m];d+=` C${(p1[0]+(p2[0]-p0[0])/6).toFixed(1)},${(p1[1]+(p2[1]-p0[1])/6).toFixed(1)} ${(p2[0]-(p3[0]-p1[0])/6).toFixed(1)},${(p2[1]-(p3[1]-p1[1])/6).toFixed(1)} ${p2[0].toFixed(1)},${p2[1].toFixed(1)}`}return d+"Z"}
function hex(x){if(x.startsWith("#")&&x.length===4)x="#"+[...x.slice(1)].map(c=>c+c).join("");return x}
function mix(a,b,f){a=hex(a);b=hex(b);const h=x=>[1,3,5].map(i=>parseInt(x.slice(i,i+2),16));const A=h(a),B=h(b);return"#"+A.map((x,i)=>Math.round(x+(B[i]-x)*f).toString(16).padStart(2,"0")).join("")}
function counts(slug,G){const n=bandCounts(slug);return G.map(g=>[...g[1]].reduce((t,b)=>t+n["AJEN".indexOf(b)],0))}
/* CALCULATION · lines drawn in a talk disk = round(rise × lines-per-× setting), or round(√rise × setting × 2.2) on the square-root scale; at least 1 */
function nLines(rise){const per=v("s-n");return Math.max(1,Math.round(st.sc==="sqrt"?Math.sqrt(rise)*per*2.2:rise*per))}

function disk(svg,slug){
 const G=TG[st.grp],cnt=counts(slug,G),t=cnt.reduce((a,b)=>a+b,0),sh=cnt.map(x=>x/t),n=sh.length;
 const c=150,R=96,INK=css("--ink"),MAG=css("--event"),PALM=st.col==="pal";
 /* palette mode: each group takes the hue at its centre on the Alarm→Normalizing axis, as in the density curves */
 let u0=0;const GC=G.map(g=>{const a=u0,b=u0+g[1].length;u0=b;return PALM?hueAt((a+b)/2,MAG):css(g[2])});
 /* spoke angles (degrees, 0 = right, clockwise): reacting groups on the left, living-with-it groups on the right */
 const step=2*Math.PI/n,an=SPOKES[st.grp].map(d=>d*Math.PI/180),ord=[...an.keys()].sort((i,j)=>an[i]-an[j]),pick=a=>ord.map(i=>a[i]);
 /* atmosphere, matching the density chart: a round dot screen, the same number of hairline rays on every disk,
    and the reacting / living-with-it split as a glowing vertical line (reacting groups sit on the left) */
 {const uid0="a"+slug,d0=el("defs",{},svg),RR=R+34;
  const bf=(id,sd)=>{const f=el("filter",{id,filterUnits:"userSpaceOnUse",x:-26,y:0,width:352,height:300},d0);el("feGaussianBlur",{stdDeviation:sd},f)};bf(uid0+"g6",5);
  if(st.ht){const pat=el("pattern",{id:uid0+"ht",width:9,height:9,patternUnits:"userSpaceOnUse",x:c,y:c},d0);el("circle",{cx:4.5,cy:4.5,r:.75,fill:INK},pat);
   const rg=el("radialGradient",{id:uid0+"rf",cx:c,cy:c,r:RR,gradientUnits:"userSpaceOnUse"},d0);[[0,1],[.65,.9],[1,0]].forEach(([o,a])=>el("stop",{offset:o,"stop-color":"#fff","stop-opacity":a},rg));
   const m=el("mask",{id:uid0+"hm",maskUnits:"userSpaceOnUse",x:-26,y:0,width:352,height:300},d0);el("circle",{cx:c,cy:c,r:RR,fill:`url(#${uid0}rf)`},m);
   el("circle",{cx:c,cy:c,r:RR,fill:`url(#${uid0}ht)`,opacity:.34,mask:`url(#${uid0}hm)`},svg)}
  if(st.rays){const nr=88;for(let k=0;k<nr;k++){const a=-Math.PI/2+k*2*Math.PI/nr,[xa,ya]=pt(c,R*.22,a),[xb,yb]=pt(c,RR+4,a);
   el("line",{x1:xa.toFixed(1),y1:ya.toFixed(1),x2:xb.toFixed(1),y2:yb.toFixed(1),stroke:INK,"stroke-width":.45,"stroke-opacity":.3},svg)}}
  const RED=css("--split");
  if(st.flare)el("line",{x1:c,x2:c,y1:c-RR-8,y2:c+RR+8,stroke:RED,"stroke-width":10,"stroke-opacity":.22,filter:`url(#${uid0}g6)`},svg);
  el("line",{x1:c,x2:c,y1:c-RR-8,y2:c+RR+8,stroke:RED,"stroke-width":.8,"stroke-opacity":.7},svg);}
 if(st.tint)an.forEach((a,i)=>{const a0=a-step/2,a1=a+step/2,r=R+22,[x0,y0]=pt(c,r,a0),[x1,y1]=pt(c,r,a1);el("path",{d:`M${c},${c}L${x0.toFixed(1)},${y0.toFixed(1)}A${r},${r} 0 0 1 ${x1.toFixed(1)},${y1.toFixed(1)}Z`,fill:GC[i],"fill-opacity":PALM?.12:.08},svg)});
 if(st.base)el("circle",{cx:c,cy:c,r:R*.16+3,fill:"none",stroke:INK,"stroke-width":.9,"stroke-dasharray":"2 2.5"},svg);
 /* the group spokes: a little bolder than the rays, same length */
 if(st.spk)an.forEach(a=>{const [xa,ya]=pt(c,R*.22,a),[x,y]=pt(c,R+38,a);el("line",{x1:xa.toFixed(1),y1:ya.toFixed(1),x2:x.toFixed(1),y2:y.toFixed(1),stroke:INK,"stroke-width":.75,"stroke-opacity":.45},svg)});
 const L=nLines(C[slug].rise),op=v("s-op")/100,w=v("s-w"),sp=v("s-sp"),tw=v("s-tw"),dr=v("s-dr"),pin=v("s-pi"),stc=v("s-st");
 const tgt=sh.map(x=>R*(.18+stc*x)),base=sh.map(()=>R*.16);
 let lx=0,ly=0;sh.forEach((x,i)=>{lx+=x*Math.cos(an[i]);ly+=x*Math.sin(an[i])});
 const dom=sh.indexOf(Math.max(...sh));
 /* palette mode: lines are drawn white into a mask, and coloured wedges (one per group) show through it;
    the last shape is also filled with the wedges, deeper where the group's share is bigger */
 let tgtEl=svg,uid="d"+slug;
 if(PALM){const defs=el("defs",{},svg),m=el("mask",{id:uid+"m",maskUnits:"userSpaceOnUse",x:-26,y:0,width:352,height:300},defs);tgtEl=m;
  makeFx(defs,uid+"f",-26,0,352,300,"4");
  const wedges=(p,op)=>an.forEach((a,i)=>{const r=R+40,[x0,y0]=pt(c,r,a-step/2),[x1,y1]=pt(c,r,a+step/2);el("path",{d:`M${c},${c}L${x0.toFixed(1)},${y0.toFixed(1)}A${r},${r} 0 0 1 ${x1.toFixed(1)},${y1.toFixed(1)}Z`,fill:GC[i],"fill-opacity":op(i)},p)});
  const cp=el("clipPath",{id:uid+"c"},defs);
  /* wedges are blurred before clipping so the hues blend inside the shape instead of meeting at a seam */
  const fb=el("filter",{id:uid+"b",filterUnits:"userSpaceOnUse",x:-26,y:0,width:352,height:300},defs);el("feGaussianBlur",{stdDeviation:9},fb);
  const gl=el("g",{filter:`url(#${uid}f)`},svg),gi=el("g",{"clip-path":`url(#${uid}c)`},gl),gib=el("g",{filter:`url(#${uid}b)`},gi);wedges(gib,i=>(.4+.6*sh[i]/Math.max(...sh)).toFixed(3));
  /* the wedges under the lines are blurred so the hues blend across each spoke instead of meeting at a seam */
  /* with Soft edge on, the masked lines are blurred slightly too, so no outline stays crisp */
  if(st.cont){
  const fs=el("filter",{id:uid+"s",filterUnits:"userSpaceOnUse",x:-26,y:0,width:352,height:300},defs);el("feGaussianBlur",{stdDeviation:1.3},fs);
  const gw=el("g",{mask:`url(#${uid}m)`},st.blur?el("g",{filter:`url(#${uid}s)`},svg):svg),gb=el("g",{filter:`url(#${uid}b)`},gw);wedges(gb,()=>1);}
  disk._cp=cp}
 for(let k=0;k<=L;k++){const f=Math.pow(k/L,sp),e=f*f*(3-2*f),rs=base.map((b,i)=>b+(tgt[i]-b)*e),last=k===L;
  let col=INK;if(PALM)col="#fff";if(st.col==="fade")col=mix(INK,MAG,e);if(st.col==="group")col=mix(INK,GC[dom],e);if(last&&!PALM)col=MAG;
  const tf=`translate(${(lx*dr*(1-e)).toFixed(1)},${(ly*dr*(1-e)).toFixed(1)}) rotate(${((1-e)*-tw).toFixed(1)},${c},${c})`;
  if(PALM&&last)el("path",{d:blob(c,pick(rs),pick(an),pin),transform:tf},disk._cp);
  el("path",{d:blob(c,pick(rs),pick(an),pin),fill:last&&st.fill&&!PALM?MAG:"none","fill-opacity":.2,stroke:col,"stroke-width":last?w*2.6:w,"stroke-opacity":last?1:Math.min(1,op*(.3+.7*f)),transform:tf},tgtEl)}
 el("circle",{cx:c,cy:c,r:2.6,fill:INK},svg);
 an.forEach((a,i)=>{const [x,y]=pt(c,R+32,a),cx=Math.cos(a),sy=Math.sin(a),anc=Math.abs(cx)<.3?"middle":cx>0?"start":"end",up=sy<-.5,dn=sy>.5;
  const y1=up?y-(st.lab?12:0):dn?y+4:y-(st.lab?3:-4);
  if(st.lab)tx(svg,{x:x.toFixed(1),y:y1.toFixed(1),"text-anchor":anc,"font-size":9.5,"letter-spacing":".26em",fill:INK,"font-weight":400},G[i][0].toUpperCase());
  if(st.pct)tx(svg,{x:x.toFixed(1),y:(y1+(st.lab?14:0)).toFixed(1),"text-anchor":anc,"font-size":14,"font-style":"italic",fill:INK,"font-family":"Cormorant Garamond,Didot,Georgia,serif"},Math.round(sh[i]*100)+"%")});
 return {G,sh,t,L,dom,GC};
}

function drawDisks(){
 const G=TG[st.grp];
 let ku=0;const KC=G.map(g=>{const a=ku,b=ku+g[1].length;ku=b;return st.col==="pal"?hueAt((a+b)/2,css("--event")):`var(${g[2]})`});
 document.getElementById("key").innerHTML=G.map((g,i)=>`<span><i style="background:${KC[i]}"></i>${g[0]}${g[3]?` <span class="v">${g[3].toLowerCase()}</span>`:""}</span>`).join("")+
  (st.col==="pal"?"":`<span class="sw"><svg viewBox="0 0 26 12" aria-hidden="true"><path d="M1 6 H25" stroke="var(--event)" stroke-width="2.4" fill="none"/></svg>worst week's split</span>`)+
  (st.base?`<span class="sw"><svg viewBox="0 0 26 12" aria-hidden="true"><path d="M1 6 H25" stroke="var(--ink)" stroke-width="1" stroke-dasharray="2 2.5" fill="none"/></svg>normal week</span>`:"");
 const grid=document.getElementById("grid");grid.innerHTML="";
 order().forEach(slug=>{const s=C[slug],fig=document.createElement("figure");fig.className="card";
  const tag=tagFor(slug);
  fig.innerHTML=`<span class="tag">${tag}</span><header><span class="nm">${s.name}<small>${s.st}</small></span><span class="x">${s.rise<10?s.rise.toFixed(1):Math.round(s.rise)}<i>×</i></span></header>
   <div class="meta"><span class="dt">${s.dates}</span><span class="it">more air talk</span></div>`;
  const svg=el("svg",{viewBox:"-26 0 352 300",role:"img"});fig.appendChild(svg);
  const r=disk(svg,slug);
  svg.setAttribute("aria-label",`${s.name}: ${r.G.map((g,i)=>`${g[0]} ${Math.round(r.sh[i]*100)}%`).join(", ")}; ${s.rise.toFixed(1)} times more air talk than normal`);
  const lead=document.createElement("p");lead.className="lead";
  lead.innerHTML=`<b style="color:${r.GC[r.dom]}">${Math.round(r.sh[r.dom]*100)}% ${r.G[r.dom][0].toLowerCase()}</b><span class="disc">${Math.round(r.t)}</span><span>comments</span>${s.fn?`<sup> ${s.fn}</sup>`:""}${slug==="bakersfield"&&st.big?" (big thread out)":""}`;
  fig.appendChild(lead);grid.appendChild(fig)});
}
const BANDS=["A","J","E","N"];
/* comment counts per tone group: Claude's draft labels on every air comment (default), or only the comments
   Dish and Gina coded by hand (agreed or reconciled). The big-thread option applies to Claude's labels only. */
/* corrected counts (Gina + Claude, Oct 6): hand-checked comments keep the agreed label, the rest are spread by how often
   Claude's label matched it, scaled to the full week. data/processed/reddit/spectrum_07_corrected/city_shares.csv (count_A..N). */
/* CORR = corrected counts A, J, E, N per city: data/tone-counts.js, corrected (scripts/site/02_tone_counts.py, from
   data/processed/reddit/spectrum_07_corrected/city_shares.csv, method = corrected, count_A..count_N). Made by
   scripts/reddit/spectrum_07_corrected_shares.py: each of the 436 hand-checked items counts once for its agreed group; each of the
   other 1,725 items is split across the groups by how often its Claude label turned out to be each agreed group among the checked
   items (one table pooled over the nine cities); sampled weeks are weighted back to the full week. */
const CORR=window.TONE.corrected;
let AUD=null;
/* CALCULATION · which counts feed the charts (st.src; the page opens on "corr"):
     corr   CORR above: corrected counts
     claude C[slug].read: Claude's draft labels, minus Bakersfield's biggest thread when that option is on
     audit  the 337 hand-coded comments (QUOTES), counted by their agreed group */
function bandCounts(slug){if(st.src==="corr")return (CORR[slug]||[0,0,0,0]).slice(); if(st.src==="audit"){if(!AUD){AUD={};QUOTES.forEach(q=>{(AUD[q.c]=AUD[q.c]||[0,0,0,0])["AJEN".indexOf(q.b)]++})}return (AUD[slug]||[0,0,0,0]).slice()}
 const s=C[slug];return BANDS.map(b=>Math.max(0,s.read[b]-(st.big&&s.big?s.big[b]:0)))}
function rng(seed){let x=0;for(const ch of seed)x=(x*31+ch.charCodeAt(0))>>>0;return()=>{x=(x*1664525+1013904223)>>>0;return x/4294967296}}
const SIG=.42;
/* gradient-curve palettes: colours spread evenly from Alarm (left) to Normalizing (right); [light, dark] */
const PAL={mag:[null,null],
 deck:[["#c4285c","#1a0f6b"],["#ff5e8e","#f8ebcb"]],
 peach:[["#f4a37a","#9b5de5","#3a1670"],["#f4a37a","#b388ff","#e6d4ff"]],
 red:[["#f0502e","#3a4fd8","#141a5c"],["#ff6b4a","#6f86ff","#c9d0ff"]],
 riso:[["#f2643c","#ec4f9a","#8a4fe0","#2a9d9a"],["#ff7a52","#ff6fb0","#a77bff","#3fc4c0"]],
 print:[["#e3301f","#ea6e62","#5638b8","#2a7a3b"],["#ff5a48","#ff9a8a","#9a84ff","#62c477"]]};
function hueAt(u,MAG){const dark=css("--ground").toLowerCase()==="#160d4c",P=PAL[st.pal][dark?1:0];if(!P)return MAG;
 const t=Math.min(1,Math.max(0,u/4))*(P.length-1),k=Math.min(P.length-2,Math.floor(t));return mix(P[k],P[k+1],t-k)}
/* CALCULATION · the tone hills: a Gaussian smoothing of the four shares.
     kde(sh, u) = Σ over groups b of  sh_b × exp( -(u - (b + 0.5))² / (2 × SIG²) ),  SIG = 0.42
   Each group adds a bell curve centred on its section, as tall as its share. The curves are not rescaled per city:
   every hill is divided by the tallest point across the cities drawn (kmax; all nine by default), so heights compare between cities. */
function kde(sh,u){return sh.reduce((t,w,b)=>t+w*Math.exp(-((u-(b+.5))**2)/(2*SIG*SIG)),0)}
/* soft edge = blur; grain = keep each pixel only where the shape is denser than a noise field, so thin parts dissolve into speckle */
function makeFx(defs,id,x,y,w,h,blur){
 const f=el("filter",{id,filterUnits:"userSpaceOnUse",x,y,width:w,height:h,"color-interpolation-filters":"sRGB"},defs);
 let src="SourceGraphic";
 if(st.blur){el("feGaussianBlur",{in:src,stdDeviation:blur,result:"bl"},f);src="bl"}
 if(st.grain){el("feTurbulence",{type:"fractalNoise",baseFrequency:"0.95",numOctaves:2,seed:7,result:"nz"},f);
  el("feColorMatrix",{in:"nz",type:"matrix",values:"0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  1.6 0 0 0 -0.3",result:"na"},f);
  el("feColorMatrix",{in:src,type:"matrix",values:"0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0",result:"sa"},f);
  el("feComposite",{in:"sa",in2:"na",operator:"arithmetic",k1:0,k2:2.4,k3:-1.4,k4:.15,result:"mask"},f);
  el("feComposite",{in:src,in2:"mask",operator:"in"},f)}
 if(!st.blur&&!st.grain)el("feOffset",{in:src,dx:0,dy:0},f);
 return f}
/* Quadrant: x = where the city's tone sits (same 0–4 axis and "Dot sits at" setting as the curves),
   y = bad-air days a year (descriptive only; square-root scale so 0–2 days are not crushed).
   Dividers: the reacting / living-with-it split, and the nine cities' median bad-air days. */
/* CALCULATION · quadrant: across = dotPos, up = √(bad-air days / 12); the dashed line = the median of the nine cities' bad-air days (5th of 9 sorted) */
function drawQuad(){
 const svg=document.getElementById("rows");svg.innerHTML="";
 const W=1000,H=660,x0=170,x1=880,X=u=>x0+(x1-x0)*u/4,yt=96,yb=560,DMAX=12,Y=d=>yb-(yb-yt)*Math.sqrt(d/DMAX);
 svg.setAttribute("viewBox",`0 0 ${W} ${H}`);
 const INK=css("--ink"),INK2=css("--ink-2"),MAG=css("--event"),RED=css("--split"),GR=css("--ground"),G=TG[st.grp];
 const FINE="Cormorant Garamond,Didot,Georgia,serif",MONO="IBM Plex Mono,monospace";
 const defs=el("defs",{},svg);
 const blurF=(id,sd)=>{const f=el("filter",{id,filterUnits:"userSpaceOnUse",x:0,y:0,width:W,height:H},defs);el("feGaussianBlur",{stdDeviation:sd},f);return f};
 blurF("q6",6);blurF("q3",3);
 const gl=blurF("q12",12);
 if(st.grain||st.blur)makeFx(defs,"qfx",0,0,W,H,"3");
 if(st.ht){const pat=el("pattern",{id:"qht",width:11,height:11,patternUnits:"userSpaceOnUse"},defs);el("circle",{cx:5.5,cy:5.5,r:.85,fill:INK},pat);
  const rg=el("radialGradient",{id:"qrf",cx:.5,cy:.5,r:.62},defs);[[0,1],[.7,.85],[1,0]].forEach(([o,a])=>el("stop",{offset:o,"stop-color":"#fff","stop-opacity":a},rg));
  const m=el("mask",{id:"qhm",maskUnits:"userSpaceOnUse",x:0,y:0,width:W,height:H},defs);el("rect",{x:x0-30,y:yt-30,width:x1-x0+60,height:yb-yt+60,fill:"url(#qrf)"},m);
  el("rect",{x:x0-30,y:yt-30,width:x1-x0+60,height:yb-yt+60,fill:"url(#qht)",opacity:.32,mask:"url(#qhm)"},svg)}
 /* group names across the top, faint section boundaries */
 const spans=[];let u=0;G.forEach(g=>{spans.push([u,u+g[1].length,g]);u+=g[1].length});
 spans.forEach(([a,b,g])=>tx(svg,{x:X((a+b)/2),y:40,"text-anchor":"middle","font-size":12.5,"letter-spacing":".34em",fill:INK},g[0].toUpperCase()));
 spans.slice(1).map(sp=>sp[0]).filter(b=>b!==2).forEach(b=>el("line",{x1:X(b),x2:X(b),y1:yt-20,y2:yb+6,stroke:INK,"stroke-width":.5,"stroke-opacity":.35,"stroke-dasharray":"1 4"},svg));
 /* vertical divider: the reacting / living-with-it split */
 const xs=X(2);
 if(st.flare)el("line",{x1:xs,x2:xs,y1:yt-34,y2:yb+14,stroke:RED,"stroke-width":12,"stroke-opacity":.28,filter:"url(#q6)"},svg);
 el("line",{x1:xs,x2:xs,y1:yt-34,y2:yb+14,stroke:RED,"stroke-width":1,"stroke-opacity":.85},svg);
 tx(svg,{x:xs-10,y:yt-16,"text-anchor":"end","font-size":15,"font-style":"italic","font-family":FINE,fill:INK2},"reacting");
 tx(svg,{x:xs+10,y:yt-16,"font-size":15,"font-style":"italic","font-family":FINE,fill:INK2},"living with it");
 /* horizontal divider: median bad-air days across the nine cities */
 const days=Object.values(C).map(c=>c.bad).sort((a,b)=>a-b),med=days[Math.floor(days.length/2)],ym=Y(med);
 el("line",{x1:x0-14,x2:x1+14,y1:ym,y2:ym,stroke:INK,"stroke-width":.7,"stroke-opacity":.6,"stroke-dasharray":"3 4"},svg);
 if(st.flare)el("ellipse",{cx:xs,cy:ym,rx:30,ry:2.4,fill:RED,"fill-opacity":.55,filter:"url(#q3)"},svg);
 tx(svg,{x:x1+16,y:ym+4,"font-size":13.5,"font-style":"italic","font-family":FINE,fill:INK2},`median, ${med} day${med===1?"":"s"}`);
 /* y axis: ticks and end labels */
 el("line",{x1:x0-34,x2:x0-34,y1:yb,y2:yt,stroke:INK,"stroke-width":.7},svg);
 el("path",{d:`M${x0-38},${yt+7} L${x0-34},${yt} L${x0-30},${yt+7}`,fill:"none",stroke:INK,"stroke-width":.7},svg);
 [0,1,2,4,8,12].forEach(d=>{el("line",{x1:x0-38,x2:x0-30,y1:Y(d),y2:Y(d),stroke:INK,"stroke-width":.7},svg);
  tx(svg,{x:x0-44,y:Y(d)+4,"text-anchor":"end","font-size":11,"font-family":MONO,fill:INK2},d)});
 tx(svg,{x:x0-34,y:yt-16,"text-anchor":"middle","font-size":15,"font-style":"italic","font-family":FINE,fill:INK},"lives with bad air");
 tx(svg,{x:x0-34,y:yb+30,"text-anchor":"middle","font-size":15,"font-style":"italic","font-family":FINE,fill:INK},"rarely has bad air");
 const yl=el("text",{x:0,y:0,transform:`translate(${x0-92},${(yt+yb)/2}) rotate(-90)`,"text-anchor":"middle","font-size":10,"letter-spacing":".3em",fill:INK2},svg);yl.textContent="BAD-AIR DAYS A YEAR";
 /* x axis arrow */
 const ya=yb+56;
 el("line",{x1:X(0),x2:X(4),y1:ya,y2:ya,stroke:INK,"stroke-width":.7},svg);
 el("path",{d:`M${X(4)-7},${ya-4} L${X(4)},${ya} L${X(4)-7},${ya+4}`,fill:"none",stroke:INK,"stroke-width":.7},svg);
 el("circle",{cx:X(0),cy:ya,r:2.5,fill:INK},svg);
 tx(svg,{x:X(0),y:ya+28,"font-size":20,"font-style":"italic","font-family":FINE,fill:INK},"Reacting");
 tx(svg,{x:X(4),y:ya+28,"text-anchor":"end","font-size":20,"font-style":"italic","font-family":FINE,fill:INK},"Living with it");
 /* cities */
 const pts=Object.keys(C).map(slug=>{const S=shares(slug);let m;
  if(st.dot==="peak")m=peakOf(S.sh);
  else if(st.dot==="med"){let cum=0,b=0;while(b<3&&cum+S.sh[b]<.5){cum+=S.sh[b];b++}m=b+(S.sh[b]?(.5-cum)/S.sh[b]:.5)}
  else m=S.sh.reduce((t,w,b)=>t+w*(b+.5),0);
  return{slug,m,t:S.t,sh:S.sh,x:X(m),y:Y(C[slug].bad)}});
 /* cities that land on the same spot are nudged apart sideways (noted in the caption) */
 pts.forEach((p,i)=>{const same=pts.filter((q,j)=>j<i&&Math.abs(q.x-p.x)<14&&Math.abs(q.y-p.y)<14);if(same.length){p.x+=12*same.length;same.forEach(q=>{q.x-=6});p.nudged=true;same.forEach(q=>q.nudged=true)}});
 const tmax=Math.max(...pts.map(p=>p.t));
 const glow=el("g",{filter:st.grain||st.blur?"url(#qfx)":null},svg);if(!(st.grain||st.blur))glow.removeAttribute("filter");
 pts.forEach(p=>{const r=18+30*Math.sqrt(p.t/tmax);el("circle",{cx:p.x.toFixed(1),cy:p.y.toFixed(1),r:r.toFixed(1),fill:hueAt(p.m,MAG),"fill-opacity":.6,filter:"url(#q12)"},glow)});
 /* labels: try right, left, below, above each dot and keep the first spot that clashes with no placed label or dot */
 const boxes=pts.map(p=>({x0:p.x-6,x1:p.x+6,y0:p.y-6,y1:p.y+6})).concat([{x0:0,x1:x0-26,y0:0,y1:H}]),hit=(b)=>boxes.some(o=>b.x0<o.x1&&b.x1>o.x0&&b.y0<o.y1&&b.y1>o.y0);
 pts.slice().sort((a,b)=>a.x-b.x).forEach(p=>{const s=C[p.slug],meta=`${s.bad} DAY${s.bad===1?"":"S"} · ${p.t} COMMENTS`,w=Math.max(s.name.length*8.4,meta.length*6.4)+4,h=28;
  const cand=[["start",p.x+10,p.y-6],["end",p.x-10,p.y-6],["middle",p.x,p.y+24],["middle",p.x,p.y-26],["start",p.x+10,p.y+26],["end",p.x-10,p.y+26]];
  let pick=cand[0];for(const c of cand){const x0=c[0]==="start"?c[1]:c[0]==="end"?c[1]-w:c[1]-w/2,bx={x0,x1:x0+w,y0:c[2]-17,y1:c[2]-17+h};if(!hit(bx)){pick=c;boxes.push(bx);break}}
  const g=el("g",{role:"img","aria-label":`${s.name}: ${s.bad} bad-air days a year; tone peaks in ${TG.four[Math.min(3,Math.floor(p.m))][0].toLowerCase()}; ${p.t} comments`},svg);
  el("circle",{cx:p.x.toFixed(1),cy:p.y.toFixed(1),r:4.5,fill:INK},g);
  tx(g,{x:pick[1].toFixed(1),y:pick[2].toFixed(1),"text-anchor":pick[0],"font-size":19,"font-style":"italic","font-family":FINE,fill:INK},s.name);
  tx(g,{x:pick[1].toFixed(1),y:(pick[2]+15).toFixed(1),"text-anchor":pick[0],"font-size":9,"letter-spacing":".2em",fill:INK2},meta)});
}
/* Quotes: the hand-audited comments (Dish + Gina agreed, or reconciled), drawn as text.
   City positions are recomputed from these audited labels (not Claude's drafts): across = where the tone sits
   ("Dot sits at" setting), up = bad-air days a year (square root). Each quote is pulled sideways toward its own
   group, and quotes toward Alarm pack tighter and tremble more. No axes or numbers. */
const QUOTES=window.HAND_CODED||[];   /* the 337 hand-coded comments: data/hand-coded-comments.js (scripts/site/01_hand_coded_comments.py) */
let qRaf=0;
/* CALCULATION · where a city's dot sits on the 0-4 axis ("Dot sits at"):
     peak     peakOf(sh), the top of its hill (the page's setting)
     median   walk Alarm -> Normalizing adding shares until the next group would pass 0.5; the point is placed inside that
              group's section in proportion: b + (0.5 - shares before it) / sh_b
     average  Σ sh_b × (b + 0.5), each comment counted at its section's centre */
function dotPos(sh){if(st.dot==="peak")return peakOf(sh);
 if(st.dot==="med"){let cum=0,b=0;while(b<3&&cum+sh[b]<.5){cum+=sh[b];b++}return b+(sh[b]?(.5-cum)/sh[b]:.5)}
 return sh.reduce((t,w,b)=>t+w*(b+.5),0)}
function gauss(r){return Math.sqrt(-2*Math.log(1-r()))*Math.cos(2*Math.PI*r())}
/* Words: from the same hand-audited comments. Each word counts once per comment.
   "Most used" ranks by how many comments in that city and tone group use it; "Most distinctive" ranks by how much
   more often that city and group use it than every other city and group (smoothed log ratio, at least 2 comments). */
/* CALCULATION · words: lower-case the comment, turn ’ into ', drop [link] and [user], keep runs of letters (with ' or -) of 3 or more
   letters, cut a final 's, and drop the stop words below. Plate "The words people chose" (cityWords) counts each word once per comment:
     n   = comments in this city and tone group that use the word
     "most used":        rank by n
     "most distinctive": rank by  ln( ((n + 0.5) / (n_k + 1)) / ((o + 0.5) / (N - n_k + 1)) ) × √n,  only for n >= 2,
         n_k = comments in this city and group, o = comments in every other city and group that use the word, N = 337 */
const STOP=new Set(("a about above after again against all also am an and any are aren't as at be because been before being below between both but by "+
 "can can't cannot could couldn't did didn't do does doesn't doing don't down during each few for from further get got had hadn't has hasn't have haven't having "+
 "he he'd he'll he's her here here's hers herself him himself his how how's i i'd i'll i'm i've if in into is isn't it it's its itself just let's like "+
 "me more most mustn't my myself no nor not now of off on once only or other ought our ours ourselves out over own really same shan't she she'd she'll she's "+
 "should shouldn't so some such than that that's the their theirs them themselves then there there's these they they'd they'll they're they've this those "+
 "through to too under until up very was wasn't we we'd we'll we're we've were weren't what what's when when's where where's which while who who's whom why "+
 "why's will with won't would wouldn't you you'd you'll you're you've your yours yourself yourselves im ive dont cant thats its youre theyre didnt doesnt "+
 "one even still much many lot lol yeah yes well also though get gets getting go going gone know think make made see say said says way thing things "+
 "really pretty sure right back today now day days time every anyone someone people link user").split(" "));
/* Word categories: a first draft by Claude, to be edited by Dish and Gina. A word belongs to the first category that lists it. */
const CATS=[
 ["Body & health","asthma breathing breathe breath allergies allergy lungs lung fever cough coughing congested congestion inhaler sick headache headaches migraine eyes throat health covid sinus wheezing nose doctor hospital pneumonia symptoms"],
 ["Protection","mask masks n95 n95s filter filters purifier purifiers respirator respirators wear wearing windows closed indoors inside stay staying hepa"],
 ["Visibility","smoke smoky smokey ash fire fires wildfire wildfires smell smells smog haze hazy fog sun sky canadian burning burn"]];
const CATOF={};CATS.forEach(([n,ws],i)=>ws.split(" ").forEach(w=>{if(!(w in CATOF))CATOF[w]=i}));
let WORDCACHE={};
function cityWords(wcat,wn){const key=st.wmode+"|"+wn+"|"+wcat;if(WORDCACHE[key])return WORDCACHE[key];
 const tok=t=>[...new Set(t.toLowerCase().replace(/[’‘]/g,"'").replace(/\[(link|user)\]/g," ").match(/[a-z][a-z'\-]*[a-z]|[a-z]{3,}/g)||[])].map(w=>w.replace(/'s$/,"")).filter(w=>w.length>=3&&!STOP.has(w));
 const cnt={},tot={},all={};let N=0;const ex={};
 QUOTES.forEach(q=>{const k=q.c+"|"+q.b;cnt[k]=cnt[k]||{};tot[k]=(tot[k]||0)+1;N++;new Set(tok(q.t)).forEach(w=>{cnt[k][w]=(cnt[k][w]||0)+1;all[w]=(all[w]||0)+1;(ex[k+"|"+w]=ex[k+"|"+w]||[]).push(q.t)})});
 const out={},TOP=wn;
 Object.keys(cnt).forEach(k=>{const [c,b]=k.split("|"),nk=tot[k];
  const sc=Object.entries(cnt[k]).map(([w,n])=>{const o=all[w]-n,no=N-nk;return{w,n,s:st.wmode==="dist"?(n>=2?Math.log(((n+.5)/(nk+1))/((o+.5)/(no+1)))*Math.sqrt(n):-1e9):n}});
  sc.sort((a,b)=>b.s-a.s||b.n-a.n||a.w.localeCompare(b.w));(out[c]=out[c]||[]);sc.filter(o=>o.s>-1e9&&(wcat==="all"||CATOF[o.w]===+wcat)).slice(0,TOP).forEach(o=>out[c].push({w:o.w,n:o.n,b,ex:ex[k+"|"+o.w]}))});
 return WORDCACHE[key]=out}
/* Word cloud: one entry per word, sized by how many times it appears in the hand-audited comments
   (every occurrence counts). Packed on a spiral from the centre, biggest words first; colour = the tone group
   whose comments use it most. */
/* CALCULATION · word cloud: every occurrence counts (a word used twice in one comment counts 2); docs = comments that use it.
   by[] = occurrences per tone group; a word's colour is the group with the most occurrences (the earlier group on a tie). Font size = (10 + 70 × √(n / n of the top word)) px × Size. */
function cloudCounts(ctx){const cnt={};
 QUOTES.forEach(q=>{if(ctx.city!=="all"&&q.c!==ctx.city)return;
  const ws=(q.t.toLowerCase().replace(/[’‘]/g,"'").replace(/\[(link|user)\]/g," ").match(/[a-z][a-z'\-]*[a-z]|[a-z]{3,}/g)||[]).map(w=>w.replace(/'s$/,"")).filter(w=>w.length>=3&&!STOP.has(w));
  const seen=new Set();ws.forEach(w=>{const o=cnt[w]=cnt[w]||{w,n:0,docs:0,by:[0,0,0,0]};o.n++;o.by["AJEN".indexOf(q.b)]++;if(!seen.has(w)){seen.add(w);o.docs++}})});
 /* topic filter: keep only the words listed under that topic */
 return Object.values(cnt).filter(o=>ctx.cat==="all"||CATOF[o.w]===+ctx.cat).sort((a,b)=>b.n-a.n||a.w.localeCompare(b.w))}
function drawCloud(ctx){
 const svg=ctx.svg;svg.innerHTML="";const W=1000,H=640;svg.setAttribute("viewBox",`0 0 ${W} ${H}`);
 const FINE="Cormorant Garamond",INK=css("--ink"),MAG=css("--event");
 const words=cloudCounts(ctx).slice(0,ctx.cn);if(!words.length)return;
 const max=words[0].n,mctx=document.createElement("canvas").getContext("2d"),SZ=ctx.csz;
 const lay=()=>{svg.innerHTML="";const boxes=[],nodes=[];
  words.forEach((o,i)=>{const TONE=st.ccol==="tone",fs=(10+70*Math.sqrt(o.n/max))*SZ;mctx.font=`${TONE?600:400} ${fs}px ${HEL}`;const w=mctx.measureText(o.w).width+fs*.12,h=fs*.78;
   let placed=null;for(let k=0;k<4000&&!placed;k++){const a=k*.21,r=1.7*a,x=W/2+r*Math.cos(a)*1.5,y=H/2+r*Math.sin(a)*.95,b={x0:x-w/2,x1:x+w/2,y0:y-h*.72,y1:y+h*.28};
    if(b.x0<6||b.x1>W-6||b.y0<6||b.y1>H-6)continue;if(!boxes.some(c=>b.x0<c.x1&&b.x1>c.x0&&b.y0<c.y1&&b.y1>c.y0))placed=b;}
   if(!placed)return;boxes.push(placed);
   const main=o.by.indexOf(Math.max(...o.by)),t=tx(svg,{x:((placed.x0+placed.x1)/2).toFixed(1),y:(placed.y1-h*.28).toFixed(1),"text-anchor":"middle","font-size":fs.toFixed(1),"font-weight":TONE?600:400,
    style:`font-family:${HEL}`,fill:TONE?toneBold(main):INK,"fill-opacity":(TONE?.85+.15*Math.sqrt(o.n/max):.55+.45*Math.sqrt(o.n/max)).toFixed(2)},o.w);
   nodes.push({o,b:placed,t})});
  /* hover: the word's count and how it splits across tone groups */
  const card=ctx.card,wrap=ctx.wrap;let hot=null;
  const clear=()=>{if(hot){hot.t.removeAttribute("text-decoration");hot=null}card.hidden=true};
  wrap.onpointerleave=clear;
  wrap.onpointermove=e=>{const m=svg.getScreenCTM();if(!m)return;const p=new DOMPoint(e.clientX,e.clientY).matrixTransform(m.inverse());
   const n=nodes.find(n=>p.x>=n.b.x0&&p.x<=n.b.x1&&p.y>=n.b.y0&&p.y<=n.b.y1);if(!n){clear();return}
   if(n!==hot){clear();hot=n;n.t.setAttribute("text-decoration","underline");
    card.querySelector(".q-t").textContent=`${n.o.w} — ${n.o.n} time${n.o.n===1?"":"s"} in ${n.o.docs} comment${n.o.docs===1?"":"s"}`;
    card.querySelector(".q-m").textContent=TG.four.map((g,i)=>`${g[0]} ${n.o.by[i]}`).join(" · ")+(ctx.city==="all"?" · all cities":" · "+C[ctx.city].name)+(n.o.w in CATOF?" · "+CATS[CATOF[n.o.w]][0]:"");card.hidden=false}
   const rb=wrap.getBoundingClientRect(),cw=card.offsetWidth,ch=card.offsetHeight;let lx=e.clientX-rb.left+14,ly=e.clientY-rb.top+14;
   if(lx+cw>rb.width)lx=e.clientX-rb.left-cw-14;if(ly+ch>rb.height)ly=e.clientY-rb.top-ch-14;card.style.left=Math.max(0,lx)+"px";card.style.top=Math.max(0,ly)+"px"}};
 /* measure with the real face once it has loaded, so the packing fits the drawn words */
 lay();
}
const HEL='"Helvetica Neue",Helvetica,Arial,sans-serif';
const toneBold=b=>css(["--tb-a","--tb-j","--tb-e","--tb-n"][b]);
/* Spread and City gap are remembered separately for Quotes and Words */
const QSL={quotes:{"q-sp":2.2,"q-gap":135},words:{"q-sp":1.6,"q-gap":120}};
function loadQSL(){const o=QSL[st.view];if(!o)return;for(const id in o){document.getElementById(id).value=o[id];document.getElementById("o-"+id).textContent=o[id]}}
let WARR=null;
/* position a node: blend its cloud spot and grid spot by n.k, with a curved path, plus motion offsets */
function place(n,dx,dy){let x=n.x,y=n.y;
 if(n.k!==undefined&&n.gx!==undefined){const k=n.k;x=n.x+(n.gx-n.x)*k;y=n.y+(n.gy-n.y)*k+Math.sin(Math.PI*k)*n.bend}
 if(n.k!==undefined&&n.cat<0)n.el.setAttribute("fill-opacity",(n.op*(1-n.k)).toFixed(3));
 n.px=x+dx;n.py=y+dy;n.el.setAttribute("transform",`translate(${n.px.toFixed(1)},${n.py.toFixed(1)})`)}
/* start the move between cloud and categories without rebuilding the drawing */
function wordsArrange(ctx){if(!ctx.warr)return;const to=ctx.wlay==="cat"?1:0,reduce=matchMedia("(prefers-reduced-motion: reduce)").matches;
 ctx.warr.nodes.forEach(n=>{n.from=n.k;n.to=to;if(reduce){n.k=to;place(n,0,0)}});ctx.warr.t0=0;
 ctx.warr.catG.style.opacity=to;ctx.warr.glowG.style.opacity=ctx.warr.nameG.style.opacity=1-to;
 if(reduce)return;if(!ctx.raf)drawQuotes(ctx)}
/* CALCULATION · quotes layout (a loose map, not a chart):
     city centre: across = average position (dotPos, "average") from the city's hand-coded comments only; up = √(bad-air days / 12)
     each quote:  u = m + (b + 0.5 - m) × 0.5 × min(Spread, 1.6) + gauss() × 0.14 × Spread   (m = city centre, b = the quote's group)
                  tremble weight j = exp(-(u - 0.5)² / (2 × 0.9²)): 1 at Alarm, near 0 by Enduring
     gauss() is a standard normal draw from a generator seeded per city, so the layout is the same on every load. */
function drawQuotes(ctx){
 const svg=ctx.svg;svg.innerHTML="";
 const W=1000,H=820,x0=150,x1=850,X=u=>x0+(x1-x0)*u/4,yt=110,yb=720,Y=d=>yb-(yb-yt)*Math.sqrt(d/12);
 svg.setAttribute("viewBox",`0 0 ${W} ${H}`);
 const INK=css("--ink"),INK2=css("--ink-2"),MAG=css("--event"),FINE="Cormorant Garamond,Didot,Georgia,serif",B="AJEN";
 const defs=el("defs",{},svg),f=el("filter",{id:"qg",filterUnits:"userSpaceOnUse",x:0,y:0,width:W,height:H},defs);el("feGaussianBlur",{stdDeviation:26},f);
 /* city positions from the audited labels */
 const byCity={};QUOTES.forEach(q=>{(byCity[q.c]=byCity[q.c]||{n:[0,0,0,0],q:[]}).n[B.indexOf(q.b)]++;byCity[q.c].q.push(q)});
 const glowG=el("g",{},svg),textG=el("g",{},svg),nameG=el("g",{},svg),nodes=[];
 const reduce=matchMedia("(prefers-reduced-motion: reduce)").matches;
 /* the quotes view always uses the average position (peak snaps several cities onto the same spot),
    then city centres that sit too close are pushed apart a little: this is a loose map, not a chart */
 /* city filter: one city fills the drawing, with its text set larger so it can be read */
 const ONE=ctx.qcity!=="all",ZS=ONE?2.1:1;
 const cen=Object.keys(C).filter(k=>byCity[k]&&(!ONE||k===ctx.qcity)).map(slug=>{const d=byCity[slug],t=d.n.reduce((a,b)=>a+b,0),sh=d.n.map(x=>x/t),m=sh.reduce((a,w,b)=>a+w*(b+.5),0);return{slug,t,sh,m,x:X(m),y:Y(C[slug].bad)}});
 for(let it=0;it<120;it++)for(const a of cen)for(const b of cen){if(a===b)continue;const dx=(b.x-a.x)/1.9,dy=b.y-a.y,dd=Math.hypot(dx,dy)||1;
  const GAP=ctx.gap;if(dd<GAP){const pu=(GAP-dd)/2*.15;a.x-=dx/dd*pu*1.9;a.y-=dy/dd*pu;b.x+=dx/dd*pu*1.9;b.y+=dy/dd*pu}}
 cen.forEach(o=>{o.y=Math.min(yb+20,Math.max(yt-20,o.y))});
 cen.forEach(({slug,t,sh,m,x:cx,y:cy})=>{const d=byCity[slug],r=rng("q"+slug),off=cx-X(m);
  const WRD=ctx.view==="words";
  if(WRD)(cityWords(ctx.wcat,ctx.wn)[slug]||[]).forEach(it=>{const b=B.indexOf(it.b);
   const SP=ctx.sp,u=m+(b+.5-m)*.5*Math.min(SP,1.6)+gauss(r)*.14*SP,j=Math.exp(-((u-.5)**2)/(2*.9*.9));
   const x=X(u)+off+gauss(r)*5*SP*(1-.5*j),y=cy+gauss(r)*24*SP*(1-.6*j);
   const TONE=st.qcol==="tone",fs=(6+4.2*Math.sqrt(it.n))*ctx.wsz*ZS,el_=tx(textG,{class:"q",x:0,y:0,"text-anchor":"middle","font-size":fs.toFixed(1),style:`font-family:${HEL}`,"font-weight":TONE?600:400,
    fill:TONE?toneBold(b):INK,"fill-opacity":((TONE?.7:.45)+(TONE?.3:.4)*Math.min(1,it.n/6)).toFixed(2),transform:`translate(${x.toFixed(1)},${y.toFixed(1)})`},it.w);
   nodes.push({el:el_,word:it,c:slug,cat:it.w in CATOF?CATOF[it.w]:-1,b,op:+el_.getAttribute("fill-opacity"),x,y,j,ph:r()*6.28,ph2:r()*6.28,sp:.6+r()*.6})});
  else d.q.forEach(q=>{const b=B.indexOf(q.b);
   const SP=ctx.sp,u=m+(b+.5-m)*.5*Math.min(SP,1.6)+gauss(r)*.14*SP,j=Math.exp(-((u-.5)**2)/(2*.9*.9));   /* j: 1 at Alarm, fading through Adjusting to ~0 by Enduring */
   const x=X(u)+off+gauss(r)*5*SP*(1-.5*j),y=cy+gauss(r)*24*SP*(1-.6*j);
   /* quotes Dish and Gina flagged as interesting: larger, fuller and stronger, drawn on top */
   const big=st.qflag&&q.f,nw=big?15:4,words=q.t.split(" "),short=words.length>nw?words.slice(0,nw).join(" ")+"…":q.t;
   const TONE=st.qcol==="tone",fs=(big?10+1.2*r():4.6+4.2*r()**2)*ZS,el_=tx(textG,{class:"q",x:0,y:0,"text-anchor":"middle","font-size":fs.toFixed(1),style:`font-family:${HEL}`,
    fill:TONE?toneBold(b):INK,"fill-opacity":big?.95:((TONE?.6:.32)+.4*r()).toFixed(2),"font-weight":big||TONE?600:400,transform:`translate(${x.toFixed(1)},${y.toFixed(1)})`},short);
   /* flagged quotes wrap onto short lines (6 words each) so they read as small blocks */
   if(big){el_.textContent="";const ws=short.split(" ");for(let k=0;k<ws.length;k+=6){const ts=document.createElementNS(NS,"tspan");ts.setAttribute("x",0);ts.setAttribute("dy",k?"1.1em":`${-(Math.ceil(ws.length/6)-1)*.55}em`);ts.textContent=ws.slice(k,k+6).join(" ");el_.appendChild(ts)}}
   nodes.push({el:el_,q,c:slug,x,y,j:big?j*.35:j,ph:r()*6.28,ph2:r()*6.28,sp:.6+r()*.6,big})});
  });
 /* Shapely packing: each city's text is set into an ellipse sized to hold it, like type filling a silhouette.
    Every item starts at its tone-leaning target and spirals out to the nearest free spot inside the shape
    (flagged quotes and big words first), so clusters have crisp edges and nothing overlaps. */
 const SPk=ctx.sp,ASP=2.1;
 nodes.forEach(n=>{const bb=n.el.getBBox();n.bx=bb.x;n.by=bb.y;n.bw=bb.width;n.bh=bb.height});
 cen.forEach(o=>{const ns=nodes.filter(n=>n.c===o.slug),area=ns.reduce((a,n)=>a+(n.bw+1.6)*n.bh,0)/.8*Math.max(.6,SPk/1.6);
  o.B=Math.sqrt(area/(Math.PI*ASP));o.A=o.B*ASP;ns.forEach(n=>{n.ox=n.x-o.x;n.oy=n.y-o.y})});
 for(let it=0;it<500;it++)for(const a of cen)for(const b of cen){if(a===b)continue;const g=ctx.gap/120,dx=b.x-a.x,dy=b.y-a.y,
  q=(dx/((a.A+b.A)*g))**2+(dy/((a.B+b.B)*g))**2;if(q<1){const k=(1-Math.sqrt(q))*.3,dd=Math.hypot(dx,dy)||1;a.x-=dx/dd*k*(a.A+b.A)*.5;a.y-=dy/dd*k*(a.B+b.B)*.5;b.x+=dx/dd*k*(a.A+b.A)*.5;b.y+=dy/dd*k*(a.B+b.B)*.5}}
 if(ONE)cen.forEach(o=>{o.x=W/2;o.y=H/2+10});
 cen.forEach(o=>{o.x=Math.min(W-o.A-6,Math.max(o.A+6,o.x));o.y=Math.min(H-o.B-6,Math.max(o.B+30,o.y))});
 const CB={};cen.forEach(o=>CB[o.slug]=o);const placed=[];
 /* keep each city name clear: reserve its spot before packing */
 if(st.qname)cen.forEach(o=>{const w=C[o.slug].name.length*7.4+20;placed.push({x0:o.x-w/2-3,x1:o.x+w/2+3,y0:o.y-o.B-24,y1:o.y-o.B-1})});
 nodes.slice().sort((a,b)=>(b.big?1e6:0)+b.bw*b.bh-((a.big?1e6:0)+a.bw*a.bh)).forEach(n=>{const o=CB[n.c];
  /* target: keep the tone lean, but squeeze it inside the shape */
  let tx_=o.x+n.ox*.8,ty_=o.y+n.oy*.5;const qq=((tx_-o.x)/(o.A*.85))**2+((ty_-o.y)/(o.B*.85))**2;if(qq>1){const s_=1/Math.sqrt(qq);tx_=o.x+(tx_-o.x)*s_;ty_=o.y+(ty_-o.y)*s_}
  const inside=(x,y,g)=>[[x+n.bx,y+n.by],[x+n.bx+n.bw,y+n.by],[x+n.bx,y+n.by+n.bh],[x+n.bx+n.bw,y+n.by+n.bh]].every(([px,py])=>((px-o.x)/(o.A*g))**2+((py-o.y)/(o.B*g))**2<=1);
  let best=null;
  /* sunflower spiral around the target: even coverage; first inside the shape, then a slightly larger shape, then anywhere */
  for(let k=0;k<24000&&!best;k++){const ph=k<8000?1:k<16000?1.25:9,kk=k%8000,rr=2.6*Math.sqrt(kk),a=kk*2.39996,x=tx_+rr*Math.cos(a)*1.4,y=ty_+rr*Math.sin(a)*.8;
   if(!inside(x,y,ph))continue;const bx={x0:x+n.bx-.8,x1:x+n.bx+n.bw+.8,y0:y+n.by,y1:y+n.by+n.bh};
   if(bx.x0<2||bx.x1>W-2||bx.y0<2||bx.y1>H-2)continue;if(!placed.some(c=>bx.x0<c.x1&&bx.x1>c.x0&&bx.y0<c.y1&&bx.y1>c.y0)){best=[x,y];placed.push(bx)}}
  if(best){n.x=best[0];n.y=best[1]}n.el.setAttribute("transform",`translate(${n.x.toFixed(1)},${n.y.toFixed(1)})`)});
 cen.forEach(o=>{if(st.qglow)el("ellipse",{cx:o.x,cy:o.y,rx:o.A*1.05,ry:o.B*1.15,fill:hueAt(o.m,MAG),"fill-opacity":.28,filter:"url(#qg)"},glowG);
  /* city name in a light, tinted pill */
  if(st.qname){const g=el("g",{},nameG),t=tx(g,{x:o.x,y:o.y-o.B-8.5,"text-anchor":"middle","font-size":10.5,"font-weight":500,"letter-spacing":".12em",style:`font-family:${HEL}`,fill:INK,"fill-opacity":.85},C[o.slug].name.toUpperCase());
   const bb=t.getBBox();g.insertBefore(el("rect",{x:(bb.x-9).toFixed(1),y:(bb.y-3.5).toFixed(1),width:(bb.width+18).toFixed(1),height:(bb.height+7).toFixed(1),rx:((bb.height+7)/2).toFixed(1),fill:INK,"fill-opacity":.1}),t)}});
 /* Words → categories: rows = categories, columns = tone groups. Each word keeps its cloud spot (x,y) and gets a
    grid spot (gx,gy) in its category row and tone column; words with no category fade out. */
 if(ctx.view==="words"){
  const gx0=230,gx1=990,gy0=78,gy1=H-14,cw=(gx1-gx0)/4,rh=(gy1-gy0)/CATS.length,catG=el("g",{id:"wcat"},svg);
  catG.style.transition="opacity 1.6s ease";catG.style.pointerEvents="none";
  TG.four.forEach((g,i)=>tx(catG,{x:gx0+cw*(i+.5),y:46,"text-anchor":"middle","font-size":12,"letter-spacing":".34em",fill:INK},g[0].toUpperCase()));
  CATS.forEach(([nm],i)=>tx(catG,{x:200,y:gy0+rh*(i+.5)+6,"text-anchor":"end","font-size":17,"font-weight":700,style:`font-family:${HEL}`,fill:INK},nm));
  const cells={};nodes.forEach(n=>{if(n.cat<0)return;(cells[n.cat+"|"+n.b]=cells[n.cat+"|"+n.b]||[]).push(n)});
  Object.entries(cells).forEach(([k,ns])=>{const [ci,bi]=k.split("|").map(Number),r=rng("cell"+k);ns.sort((a,b)=>b.word.n-a.word.n);
   ns.forEach((n,i)=>{const sp=Math.min(1,.25+i/ns.length);n.gx=gx0+cw*(bi+.5)+(r()-.5)*cw*.82*sp;n.gy=gy0+rh*(ci+.5)+(r()-.5)*rh*.7*sp})});
  nodes.forEach(n=>{n.bend=(rng(n.word.w+n.c)()-.5)*120;n.delay=rng(n.c+n.word.w)()*.6;n.k=ctx.wlay==="cat"?1:0;n.from=n.k;n.to=n.k});
  catG.style.opacity=ctx.wlay==="cat"?1:0;glowG.style.transition=nameG.style.transition="opacity 1.2s ease";glowG.style.opacity=nameG.style.opacity=ctx.wlay==="cat"?0:1;
  ctx.warr={nodes,catG,glowG,nameG,t0:0};
 }else ctx.warr=null;
 /* hover: bring a quote forward and show it in full */
 const card=ctx.card,wrap=ctx.wrap;
 nodes.filter(n=>n.big).forEach(n=>textG.appendChild(n.el));
 /* hover by hit box, not by glyph: small italic text is hard to land on, wrapped quotes are split into tspans,
    and city names sit on top. Each quote's box is measured once; its current position follows the motion. */
 nameG.style.pointerEvents="none";glowG.style.pointerEvents="none";
 nodes.forEach(n=>{const bb=n.el.getBBox();n.bx=bb.x;n.by=bb.y;n.bw=bb.width;n.bh=bb.height;n.px=n.x;n.py=n.y});
 const pick=(e)=>{const m=svg.getScreenCTM();if(!m)return null;const p=new DOMPoint(e.clientX,e.clientY).matrixTransform(m.inverse());let best=null,bd=1e9;
  for(const n of nodes){if(n.cat<0&&n.k>.5)continue;const x0=n.px+n.bx-3,y0=n.py+n.by-3;if(p.x>=x0&&p.x<=x0+n.bw+6&&p.y>=y0&&p.y<=y0+n.bh+6){const d=Math.hypot(p.x-(n.px+n.bx+n.bw/2),(p.y-(n.py+n.by+n.bh/2))*2);if(d<bd){bd=d;best=n}}}
  return best};
 let hotN=null;
 const clear=()=>{if(hotN){hotN.hot=false;hotN.el.classList.remove("hot");hotN=null}card.hidden=true};
 wrap.onpointermove=e=>{const n=pick(e);if(!n){clear();return}
  if(n!==hotN){clear();hotN=n;n.hot=true;n.el.classList.add("hot");textG.appendChild(n.el);
   if(n.word){const it=n.word,eg=it.ex.slice(0,2).map(t=>{const i=t.toLowerCase().replace(/[’‘]/g,"'").indexOf(it.w);if(i<0)return t.length>120?t.slice(0,120)+"…":t;const a=Math.max(0,i-60);return(a?"…":"")+t.slice(a,i+it.w.length+60).trim()+(i+it.w.length+60<t.length?"…":"")});
    card.querySelector(".q-t").textContent=`${it.w} — ${eg.join("  ·  ")}`;card.querySelector(".q-m").textContent=`${it.n} comment${it.n===1?"":"s"} · ${C[n.c].name} · ${TG.four[B.indexOf(it.b)][0]}${n.cat>=0?" · "+CATS[n.cat][0]:""}`}
   else{card.querySelector(".q-t").textContent=n.q.t;card.querySelector(".q-m").textContent=`Reddit · ${C[n.q.c].name} · ${TG.four[B.indexOf(n.q.b)][0]}`}card.hidden=false}
  const rb=wrap.getBoundingClientRect(),cw=card.offsetWidth,ch=card.offsetHeight;let lx=e.clientX-rb.left+14,ly=e.clientY-rb.top+14;
  if(lx+cw>rb.width)lx=e.clientX-rb.left-cw-14;if(ly+ch>rb.height)ly=e.clientY-rb.top-ch-14;card.style.left=Math.max(0,lx)+"px";card.style.top=Math.max(0,ly)+"px"};
 wrap.onpointerleave=clear;
 /* motion: a slow drift for every quote, plus a fast tremble that grows toward the split */
 if(reduce&&ctx.warr)nodes.forEach(n=>{place(n,0,0)});
 if((st.qmove||ctx.warr)&&!reduce){const step=ts=>{const mv=st.qmove?1:0,SPD=ctx.spd,DR=ctx.dr*mv,TR=ctx.tr*mv,t=ts/1000*SPD;
   if(ctx.warr&&!ctx.warr.t0)ctx.warr.t0=ts;
   for(const n of nodes){if(n.hot)continue;const dx=Math.sin(t*.35*n.sp+n.ph)*5*DR+Math.sin(t*(7+11*n.j)+n.ph2)*(.2+2.4*n.j)*TR,dy=Math.cos(t*.28*n.sp+n.ph)*3.5*DR+Math.cos(t*(8+12*n.j)+n.ph)*(.2+2*n.j)*TR;
    if(ctx.warr){const pr=Math.min(1,Math.max(0,((ts-ctx.warr.t0)/1000-n.delay)/2)),e=pr<.5?2*pr*pr:1-Math.pow(-2*pr+2,2)/2;n.k=n.from+(n.to-n.from)*e}
    place(n,dx,dy)}
   ctx.raf=requestAnimationFrame(step)};ctx.step=step;ctx.raf=requestAnimationFrame(step)}
 /* readable list of every audited quote */
 const body=ctx.list;if(body){body.innerHTML="";
 orderFor(ctx.ord).forEach(slug=>{const d=byCity[slug];if(!d)return;const h=document.createElement("div");h.className="ql-city";h.textContent=`${C[slug].name}`;body.appendChild(h);
  [...B].forEach((b,bi)=>{const qs=d.q.filter(q=>q.b===b);if(!qs.length)return;const g=document.createElement("div");g.className="ql-band";g.textContent=`${TG.four[bi][0]} · ${qs.length}`;body.appendChild(g);
   const ul=document.createElement("ul");qs.forEach(q=>{const li=document.createElement("li");li.textContent=q.t;if(q.f){li.classList.add("flag");li.title="Flagged by Dish and Gina"}ul.appendChild(li)});body.appendChild(ul)})});
 ctx.listSum.textContent=`Read all ${QUOTES.length} audited quotes`}
}
function drawRows(){
 const svg=document.getElementById("d-svg");svg.innerHTML="";
 const W=1000,x0=210,x1=900,X=u=>x0+(x1-x0)*u/4,top=78,dens=st.view==="dens",rh=dens?82:58,ordr=order(),bot=top+ordr.length*rh,H=bot+86;
 svg.setAttribute("viewBox",`0 0 ${W} ${H}`);
 const INK=css("--ink"),INK2=css("--ink-2"),MAG=css("--event"),RED=css("--split"),GR=css("--ground"),G=TG[st.grp];
 const FINE="Cormorant Garamond,Didot,Georgia,serif",MONO="IBM Plex Mono,monospace";
 /* group spans along the 0–4 axis, and the boundaries between them */
 const spans=[];let u=0;G.forEach(g=>{spans.push([u,u+g[1].length,g]);u+=g[1].length});
 const bounds=spans.slice(1).map(sp=>sp[0]);
 const data=ordr.map(slug=>{const n=bandCounts(slug),t=n.reduce((a,b)=>a+b,0);return{slug,n,t,sh:n.map(x=>x/t)}});
 const grid=[...Array(161)].map((_,i)=>i/40);
 const kmax=Math.max(...data.map(d=>Math.max(...grid.map(g=>kde(d.sh,g)))));
 const gshare=d=>spans.map(([a,b])=>d.sh.slice(a,b).reduce((x,y)=>x+y,0)),gmax=Math.max(...data.map(d=>Math.max(...gshare(d))));
 const tmax=Math.max(...data.map(d=>d.t));
 const defs=el("defs",{},svg);
 if(dens&&st.den==="gcurve"&&(st.grain||st.blur))makeFx(defs,"fx",0,0,W,H,"4 5");
 const blurF=(id,sd)=>{const f=el("filter",{id,filterUnits:"userSpaceOnUse",x:0,y:0,width:W,height:H},defs);el("feGaussianBlur",{stdDeviation:sd},f)};
 blurF("glow6",6);blurF("glow3",3);
 /* halftone ground: a fine dot screen over the plot, fading out at its left and right ends */
 if(st.ht){const pat=el("pattern",{id:"ht",width:11,height:11,patternUnits:"userSpaceOnUse"},defs);el("circle",{cx:5.5,cy:5.5,r:.85,fill:INK},pat);
  const fg=el("linearGradient",{id:"htf",x1:0,x2:1,y1:0,y2:0},defs);[[0,0],[.12,1],[.88,1],[1,0]].forEach(([o,a])=>el("stop",{offset:o,"stop-color":"#fff","stop-opacity":a},fg));
  const m=el("mask",{id:"htm",maskUnits:"userSpaceOnUse",x:0,y:0,width:W,height:H},defs);el("rect",{x:X(0)-40,y:top-24,width:X(4)-X(0)+80,height:bot-top+40,fill:"url(#htf)"},m);
  el("rect",{x:X(0)-40,y:top-24,width:X(4)-X(0)+80,height:bot-top+40,fill:"url(#ht)",opacity:.32,mask:"url(#htm)"},svg)}
 /* the split between reacting and living with it: a glowing vertical line through every row */
 const xs=X(2);
 if(st.flare){el("line",{x1:xs,x2:xs,y1:top-30,y2:bot+10,stroke:RED,"stroke-width":12,"stroke-opacity":.28,filter:"url(#glow6)"},svg)}
 el("line",{x1:xs,x2:xs,y1:top-30,y2:bot+10,stroke:RED,"stroke-width":st.flare?1:1.4,"stroke-opacity":.85},svg);
 bounds.filter(b=>b!==2).forEach(b=>el("line",{x1:X(b),x2:X(b),y1:top-14,y2:bot+4,stroke:INK,"stroke-width":.5,"stroke-opacity":.35,"stroke-dasharray":"1 4"},svg));
 /* group names: widely spaced small caps */
 spans.forEach(([a,b,g])=>tx(svg,{x:X((a+b)/2),y:32,"text-anchor":"middle","font-size":12.5,"font-weight":400,"letter-spacing":".34em",fill:INK},g[0].toUpperCase()));
 if(st.grp!=="four")spans.forEach(([a,b,g])=>g[3]&&tx(svg,{x:X((a+b)/2),y:52,"text-anchor":"middle","font-size":14,"font-style":"italic","font-family":FINE,fill:INK2},g[3].toLowerCase()));
 tx(svg,{x:W,y:top-26,"text-anchor":"end","font-size":14,"font-style":"italic","font-family":FINE,fill:INK2},"comments");
 const pts=[];
 data.forEach((d,i)=>{const s=C[d.slug],yc=top+i*rh+rh/2+(dens?8:0),cv=st.den==="curve"||st.den==="gcurve",ty=dens&&cv?yc+14:yc;
  tx(svg,{x:0,y:ty-6,"font-size":23,"font-style":"italic","font-weight":400,"font-family":FINE,fill:INK},s.name);
  tx(svg,{x:0,y:ty+11,"font-size":9.5,"letter-spacing":".2em",fill:INK2},s.dates.toUpperCase());
  /* comment count in a small ink disc */
  el("circle",{cx:W-16,cy:ty-4,r:15,fill:INK},svg);
  tx(svg,{x:W-16,y:ty-.5,"text-anchor":"middle","font-size":10.5,"font-family":MONO,fill:GR},Math.round(d.t));
  /* dot position on the 0–4 axis. peak = highest point of the smoothed curve (matches the density hills);
     median = where half the comments are on each side, spreading each group evenly across its section;
     average = each comment counted at its section's centre */
  const react=d.sh[0]+d.sh[1];let mean;
  if(st.dot==="peak")mean=grid.reduce((b,u)=>kde(d.sh,u)>kde(d.sh,b)?u:b,0);
  else if(st.dot==="med"){let cum=0,b=0;while(b<3&&cum+d.sh[b]<.5){cum+=d.sh[b];b++}mean=b+(d.sh[b]?(.5-cum)/d.sh[b]:.5)}
  else mean=d.sh.reduce((t,w,b)=>t+w*(b+.5),0);
  pts.push([X(mean),ty,mean]);
  const g=el("g",{role:"img","aria-label":`${s.name}: ${BANDS.map((b,k)=>`${TG.four[k][0]} ${Math.round(d.sh[k]*100)}%`).join(", ")}`},svg);
  if(dens){
   const bh=26,yt=yc-bh/2;
   if(st.den==="grad"){const id="gr"+i,lg=el("linearGradient",{id,gradientUnits:"userSpaceOnUse",x1:X(0),x2:X(4),y1:0,y2:0},defs);
    grid.filter((_,k)=>k%2===0).forEach(u=>el("stop",{offset:(u/4).toFixed(3),"stop-color":MAG,"stop-opacity":(kde(d.sh,u)/kmax).toFixed(3)},lg));
    el("rect",{x:X(0),y:yt,width:X(4)-X(0),height:bh,rx:bh/2,fill:`url(#${id})`},g)}
   if(st.den==="block")spans.forEach(([a,b])=>{const v=d.sh.slice(a,b).reduce((x,y)=>x+y,0);
    el("rect",{x:X(a)+1,y:yt,width:X(b)-X(a)-2,height:bh,fill:MAG,"fill-opacity":(v/gmax).toFixed(3)},g);
    tx(g,{x:X((a+b)/2),y:yt+bh+12,"text-anchor":"middle","font-size":10.5,"font-family":MONO,fill:INK2},Math.round(v*100)+"%")});
   if(st.den==="dots"){const r=rng(d.slug);BANDS.forEach((_,b)=>{const k=st.dn==="pct"?Math.round(d.sh[b]*100):d.n[b];
    for(let j=0;j<k;j++)el("circle",{cx:(X(b+.04+.92*r())).toFixed(1),cy:(yt+2+(bh-4)*r()).toFixed(1),r:st.dn==="pct"?2.3:1.9,fill:MAG,"fill-opacity":.75},g)})}
   if(cv){const base=yc+14,hh=50,cp=grid.map(u=>[X(u),base-hh*kde(d.sh,u)/kmax]);let fill=MAG,fo=.28,stroke=MAG;
    /* gradient curve: the hill's height and its colour depth both follow the density */
    if(st.den==="gcurve"){const id="gc"+i,lg=el("linearGradient",{id,gradientUnits:"userSpaceOnUse",x1:X(0),x2:X(4),y1:0,y2:0},defs);
     grid.filter((_,k)=>k%2===0).forEach(u=>el("stop",{offset:(u/4).toFixed(3),"stop-color":hueAt(u,MAG),"stop-opacity":(.08+.92*kde(d.sh,u)/kmax).toFixed(3)},lg));
     fill=`url(#${id})`;fo=1;stroke="none"}
    const path=el("path",{d:`M${X(0)},${base} `+cp.map(p=>`L${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ")+` L${X(4)},${base}Z`,fill,"fill-opacity":fo,stroke,"stroke-width":1.6},g);
    if(st.den==="gcurve"&&(st.grain||st.blur))path.setAttribute("filter","url(#fx)")}
  }
  /* hairline baseline, with a small flare where it crosses the split */
  el("line",{x1:X(0)-14,x2:X(4)+14,y1:ty,y2:ty,stroke:INK,"stroke-width":.6,"stroke-opacity":.55},g);
  if(st.flare)el("ellipse",{cx:xs,cy:ty,rx:26,ry:2.2,fill:RED,"fill-opacity":.55,filter:"url(#glow3)"},g);
  bounds.filter(b=>b!==2).forEach(b=>el("line",{x1:X(b),x2:X(b),y1:ty-5,y2:ty+5,stroke:INK,"stroke-width":.8},g));
  if(!dens&&st.pctl){const rr=st.size?4+10*Math.sqrt(d.t/tmax):7;tx(g,{x:X(mean).toFixed(1),y:ty-rr-7,"text-anchor":"middle","font-size":13,"font-style":"italic","font-family":FINE,fill:INK2},Math.round(react*100)+"% reacting")}
 });
 /* glowing thread through every city's dot: a smooth curve, coloured by the palette hue at each dot */
 if(st.link&&pts.length>1){
  const lg=el("linearGradient",{id:"thr",gradientUnits:"userSpaceOnUse",x1:0,x2:0,y1:pts[0][1],y2:pts[pts.length-1][1]},defs);
  pts.forEach(p=>el("stop",{offset:((p[1]-pts[0][1])/(pts[pts.length-1][1]-pts[0][1])).toFixed(3),"stop-color":hueAt(p[2],MAG)},lg));
  let d=`M${pts[0][0].toFixed(1)},${pts[0][1]}`;
  for(let i=0;i<pts.length-1;i++){const p0=pts[Math.max(0,i-1)],p1=pts[i],p2=pts[i+1],p3=pts[Math.min(pts.length-1,i+2)];
   d+=` C${(p1[0]+(p2[0]-p0[0])/6).toFixed(1)},${(p1[1]+(p2[1]-p0[1])/6).toFixed(1)} ${(p2[0]-(p3[0]-p1[0])/6).toFixed(1)},${(p2[1]-(p3[1]-p1[1])/6).toFixed(1)} ${p2[0].toFixed(1)},${p2[1]}`}
  el("path",{d,fill:"none",stroke:"url(#thr)","stroke-width":18,"stroke-opacity":.5,"stroke-linecap":"round",filter:"url(#glow6)"},svg);
  el("path",{d,fill:"none",stroke:"url(#thr)","stroke-width":1,"stroke-opacity":.6},svg)}
 /* dots on top */
 if(!dens||st.avg)pts.forEach((p,i)=>{const t=data[i].t,rr=!dens?(st.size?4+10*Math.sqrt(t/tmax):7):5;
  if(st.link)el("circle",{cx:p[0].toFixed(1),cy:p[1],r:rr+7,fill:hueAt(p[2],MAG),"fill-opacity":.45,filter:"url(#glow3)"},svg);
  el("circle",{cx:p[0].toFixed(1),cy:p[1],r:rr,fill:INK},svg)});
 const ya=bot+30;
 el("line",{x1:X(0)-14,x2:X(4)+14,y1:ya,y2:ya,stroke:INK,"stroke-width":.7},svg);
 el("path",{d:`M${X(4)+8},${ya-4} L${X(4)+15},${ya} L${X(4)+8},${ya+4}`,fill:"none",stroke:INK,"stroke-width":.7},svg);
 el("circle",{cx:X(0)-14,cy:ya,r:2.5,fill:INK},svg);
 tx(svg,{x:X(0)-14,y:ya+28,"font-size":20,"font-style":"italic","font-family":FINE,fill:INK},"Reacting");
 tx(svg,{x:X(4)+14,y:ya+28,"text-anchor":"end","font-size":20,"font-style":"italic","font-family":FINE,fill:INK},"Living with it");
}

/* ---------- site plates ---------- */
Object.assign(st,{view:"dens",den:"gcurve",grp:"four",ord:"bad",pal:"riso",src:"corr",dot:"peak",avg:true,grain:false,blur:false,ht:false,flare:false,link:false,big:false,
  qcol:"tone",qname:true,qglow:false,qmove:true,qflag:true,wmode:"freq"});
const mk=p=>({ord:"bad",dr:.3,tr:.5,spd:.5,wn:11,wsz:1,cn:150,csz:1,svg:document.getElementById(p+"-svg"),wrap:document.getElementById(p+"-wrap"),card:document.getElementById(p+"-card"),raf:0,step:null,warr:null,qcity:"all",wcat:"all",wlay:"cloud",city:"all",cat:"all"});
function orderFor(o){const keep=st.ord;st.ord=o;const r=order();st.ord=keep;return r}
const QC=Object.assign(mk("q"),{view:"quotes",sp:2.2,gap:135,list:document.getElementById("q-list"),listSum:document.getElementById("q-sum")});
const WC=Object.assign(mk("w"),{view:"words",sp:1.6,gap:120});
const CC=mk("c");
function keyHTML(){return TG.four.map((g,i)=>`<span><i style="background:${toneBold(i)}"></i>${g[0]}</span>`).join("")}
function drawAll(){drawRows();[QC,WC].forEach(c=>{if(c.raf)cancelAnimationFrame(c.raf);c.raf=0;drawQuotes(c)});drawCloud(CC);
  ["q-key","w-key","c-key"].forEach(id=>document.getElementById(id).innerHTML=keyHTML())}
/* labels toggle on the density plate (Gina, Oct 6): corrected (default) or Claude's draft */
const SRC_NOTE={corr:"Corrected: comments Dish and Gina checked keep their label; the rest are spread by how often Claude's label matched theirs, then scaled to the full week.",
  claude:"Claude's draft labels, uncorrected (Eugene, Seattle and Pittsburgh are 400-comment samples)."};
function syncSrc(){document.querySelectorAll(".src-tg [data-src]").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.src===st.src)));const n=document.getElementById("src-note");if(n)n.textContent=SRC_NOTE[st.src]||""}
document.querySelectorAll(".src-tg [data-src]").forEach(b=>b.addEventListener("click",()=>{st.src=b.dataset.src;syncSrc();drawRows()}));
syncSrc();
/* dropdowns */
document.getElementById("q-city").addEventListener("change",e=>{QC.qcity=e.target.value;cancelAnimationFrame(QC.raf);QC.raf=0;drawQuotes(QC)});
document.getElementById("w-city").addEventListener("change",e=>{WC.qcity=e.target.value;cancelAnimationFrame(WC.raf);WC.raf=0;drawQuotes(WC)});
document.getElementById("c-city").addEventListener("change",e=>{CC.city=e.target.value;drawCloud(CC)});
/* topic pills */
[["w",i=>{WC.wcat=i?String(i-1):"all";cancelAnimationFrame(WC.raf);WC.raf=0;drawQuotes(WC)}],["c",i=>{CC.cat=i?String(i-1):"all";drawCloud(CC)}]].forEach(([p,fn])=>{
  const tp=document.getElementById(p+"-topic"),bs=[...tp.querySelectorAll("button")];
  const set=i=>{tp.style.setProperty("--i",i);bs.forEach((b,k)=>{b.setAttribute("aria-checked",k===i);b.tabIndex=k===i?0:-1});fn(i)};
  bs.forEach((b,i)=>{b.addEventListener("click",()=>set(i));b.addEventListener("keydown",e=>{const d=e.key==="ArrowRight"||e.key==="ArrowDown"?1:e.key==="ArrowLeft"||e.key==="ArrowUp"?-1:0;if(d){e.preventDefault();set((i+d+4)%4);bs[(i+d+4)%4].focus()}})});
  bs.forEach((b,k)=>b.tabIndex=k?-1:0)});
/* order dropdowns (Quotes: the order of the full list) and sliders, each plate keeps its own */
[["q",QC],["w",WC],["c",CC]].forEach(([p,c])=>{document.getElementById(p+"-ord").addEventListener("change",e=>{c.ord=e.target.value;if(c===QC){cancelAnimationFrame(QC.raf);QC.raf=0;drawQuotes(QC)}});
  document.querySelectorAll(`[id^="${p}-"][data-k]`).forEach(i=>i.addEventListener("input",()=>{const k=i.dataset.k;c[k]=+i.value;document.getElementById(`o-${p}-${k}`).textContent=i.value;
   if(["dr","tr","spd"].includes(k))return;if(c===CC)drawCloud(CC);else{cancelAnimationFrame(c.raf);c.raf=0;drawQuotes(c)}}))});
/* cloud / categories switch */
document.getElementById("w-sw").addEventListener("change",e=>{WC.wlay=e.target.checked?"cat":"cloud";wordsArrange(WC)});
/* only animate the plates that are on screen */
const io=new IntersectionObserver(es=>es.forEach(en=>{const c=en.target.id==="q-wrap"?QC:WC;
  if(en.isIntersecting){if(!c.raf&&c.step)c.raf=requestAnimationFrame(c.step)}else if(c.raf){cancelAnimationFrame(c.raf);c.raf=0}}),{rootMargin:"80px"});
io.observe(document.getElementById("q-wrap"));io.observe(document.getElementById("w-wrap"));
matchMedia("(prefers-color-scheme: dark)").addEventListener("change",drawAll);
new MutationObserver(drawAll).observe(document.documentElement,{attributes:true,attributeFilter:["data-theme"]});
drawAll();
})();
