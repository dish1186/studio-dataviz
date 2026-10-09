/* Boiling Frog · city panel (Gina + Claude). Opens under the Plate V map when Bakersfield, Detroit, Eugene or San Jose
   is clicked. Reads window.CP_AIR (city-panel-data.js) and Bidisha's US_STATES; does not change her map code. */
(() => {
const AIR=window.CP_AIR,STATES=window.US_STATES;
const CITIES={bakersfield:{lat:35.37,lon:-119.02,st:"CA"},detroit:{lat:42.33,lon:-83.05,st:"MI"},eugene:{lat:44.05,lon:-123.09,st:"OR"},sanjose:{lat:37.34,lon:-121.89,st:"CA"}};
Object.keys(CITIES).forEach(k=>Object.assign(CITIES[k],{name:AIR[k].name,pm:AIR[k].pm,normal:AIR[k].normal}));
const STNAME={CA:"California",MI:"Michigan",OR:"Oregon"};
let current=null;
const TALK={bakersfield:{read:{A:15,J:5,E:22,N:9},est:{A:15,J:5,E:22,N:9},big:{A:0,J:0,E:18,N:8},rise:4.809},
 detroit:{read:{A:138,J:87,E:5,N:14},est:{A:138,J:87,E:5,N:14},big:{A:38,J:40,E:2,N:4},rise:26.432},
 eugene:{read:{A:144,J:160,E:5,N:13},est:{A:423.3,J:470.4,E:13.8,N:38.7},big:{A:17.6,J:29.4,E:0,N:0},rise:20.222,sampled:true},
 sanjose:{read:{A:128,J:138,E:6,N:14},est:{A:128,J:138,E:6,N:14},big:{A:6,J:13,E:0,N:0},rise:27.326}};
const CHAR={economy:"[Filler] One line on what the city runs on: main industries and employers.",politics:"[Filler] One line on local politics and how the region votes.",people:"[Filler] One line on who lives here: size, age, how long people stay."};
const cv=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const NS="http://www.w3.org/2000/svg",E=(t,a,p)=>{const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);p&&p.appendChild(e);return e},T=(p,a,s)=>{const e=E("text",a,p);e.textContent=s;return e};
/* ================= controls ================= */
let uid=0;
function controls(host,spec,st,redraw){host.innerHTML="";const rows=[];
 spec.forEach(it=>{if(it.type==="head"){const h=document.createElement("div");h.className="gh";h.textContent=it.label;host.appendChild(h);rows.push({it,row:h});return}
  const row=document.createElement("div");row.className="crow";host.appendChild(row);
  if(it.type==="seg"){const l=document.createElement("span");l.className="cl";l.textContent=it.label;row.appendChild(l);const g=document.createElement("div");g.className="seg";row.appendChild(g);
   it.opts.forEach(([v,t])=>{const b=document.createElement("button");b.type="button";b.textContent=t;b.dataset.v=v;b.addEventListener("click",()=>{st[it.key]=v;sync();redraw()});g.appendChild(b)})}
  if(it.type==="tog"){const b=document.createElement("button");b.type="button";b.className="tg";b.textContent=it.label;b.addEventListener("click",()=>{st[it.key]=!st[it.key];if(it.after)it.after(st);sync();redraw()});row.appendChild(b)}
  if(it.type==="sl"){const id="c"+(++uid),l=document.createElement("label");l.className="cl";l.htmlFor=id;l.textContent=it.label;const i=document.createElement("input");i.type="range";i.id=id;i.min=it.min;i.max=it.max;i.step=it.step;i.value=st[it.key];const o=document.createElement("output");o.textContent=st[it.key];
   i.addEventListener("input",()=>{st[it.key]=+i.value;o.textContent=i.value;if(it.after)it.after(st);sync();redraw()});row.append(l,i,o)}
  rows.push({it,row})});
 function sync(){rows.forEach(({it,row})=>{if(it.when)row.hidden=!it.when(st);row.querySelectorAll("[data-v]").forEach(b=>b.setAttribute("aria-pressed",String(st[it.key])===b.dataset.v));const t=row.querySelector(".tg");if(t)t.setAttribute("aria-pressed",!!st[it.key]);const i=row.querySelector("input");if(i&&+i.value!==st[it.key]){i.value=st[it.key];row.querySelector("output").textContent=st[it.key]}})}
 sync();return sync}

/* ================= air disk ================= */
const BANDS=[[0,9,"#f0ee9a"],[9,35.5,"#c9c7e6"],[35.5,55.5,"#eeb3c6"],[55.5,1e9,"#cf3f6c"]];
const flatCol=v=>v>35.5?cv("--event"):v>15?cv("--cp-mid"):cv("--cp-norm");
const catCol=v=>v>=55.5?cv("--event"):v>=35.5?"#e07a9a":v>9?cv("--ink"):cv("--ink-2");
const AIRSPEC=[
 {type:"head",label:"Marks"},{type:"seg",key:"mark",label:"Draw as",opts:[["line","Lines"],["dot","Dots · height"],["flat","Dots · colour"]]},
 {type:"sl",key:"ds",label:"Dot size",min:.5,max:5,step:.1,when:s=>s.mark!=="line"},
 {type:"seg",key:"res",label:"Resolution",opts:[["day","Daily"],["week","Weekly"]]},
 {type:"seg",key:"stat",label:"Each line",opts:[["med","Median"],["mean","Mean"],["p90","90th"],["max","Max"]],when:s=>s.shape==="year"},
 {type:"head",label:"Scale"},{type:"seg",key:"scale",label:"Scale",opts:[["lin","Linear"],["sqrt","Square root"],["log","Log"]]},
 {type:"tog",key:"breakout",label:"Let worst week break out"},
 {type:"seg",key:"brklen",label:"Break-out length",opts:[["grow","Grows with how far over"],["same","Same for every city"]],when:s=>s.breakout&&s.shape==="year"},
 {type:"tog",key:"mult",label:"Label as × the EPA line",when:s=>s.breakout&&s.shape==="year"},
 {type:"seg",key:"base",label:"Lines start at",opts:[["zero","Zero"],["normal","City's normal"],["who","WHO 15 line"]],when:s=>s.shape==="year"},
 {type:"seg",key:"nsrc",label:"Which normal",opts:[["study","Worst week's month (study)"],["month","Each month's own"]],when:s=>s.shape==="year"&&s.base==="normal"},
 {type:"seg",key:"range",label:"Scale range",opts:[["all","Everyday air · all cities"],["city","Everyday air · this city"],["fixed","Fixed (Clip at)"]]},
 {type:"sl",key:"clip",label:"Clip at",min:20,max:480,step:10,when:s=>s.range==="fixed"},
 {type:"head",label:"Worst week"},{type:"seg",key:"ev",label:"Show as",opts:[["spikes","Week, at its average"],["needle","One needle"],["off","Hide"]],when:s=>s.shape==="year"},
 {type:"tog",key:"top",label:"Worst week at 12 o'clock"},
 {type:"head",label:"Spiral",when:s=>s.shape==="spiral"},{type:"tog",key:"even",label:"Even out the centre",when:s=>s.shape==="spiral"},{type:"sl",key:"h",label:"Spike height",min:.3,max:3,step:.1,when:s=>s.shape==="spiral"&&s.mark!=="flat"},
 {type:"head",label:"Reference rings",when:s=>s.mark!=="flat"},{type:"tog",key:"epa",label:"EPA 35.5",when:s=>s.mark!=="flat"},{type:"tog",key:"who",label:"WHO 15",when:s=>s.shape==="year"&&s.mark!=="flat"},{type:"tog",key:"unh",label:"Unhealthy 55.5",when:s=>s.shape==="year"&&s.mark!=="flat"},{type:"tog",key:"band",label:"Category bands",when:s=>s.shape==="year"},{type:"tog",key:"norm",label:"City's normal",when:s=>s.shape==="year"&&s.mark!=="flat"},
 {type:"head",label:"Look"},{type:"seg",key:"col",label:"Colour",opts:[["level","WHO / EPA level"],["dev","Above / below normal"],["ink","Ink"],["cat","By category"],["cov","Fade by coverage"]]},{type:"tog",key:"fill",label:"Fill under the line",when:s=>s.shape==="year"&&s.mark==="line"},
 {type:"sl",key:"w",label:"Weight",min:.3,max:2.5,step:.1},{type:"sl",key:"hole",label:"Hole",min:0,max:120,step:5},{type:"tog",key:"mon",label:"Month letters"},{type:"tog",key:"ctr",label:"Centre label"}];
const airDefaults=shape=>({shape,mark:shape==="spiral"?"flat":"line",ds:shape==="spiral"?1.6:1,res:shape==="spiral"?"week":"day",stat:"med",scale:"lin",clip:480,range:"all",fill:false,ev:"spikes",nsrc:"study",breakout:true,brklen:"grow",mult:true,base:"zero",top:false,even:true,h:1,epa:true,who:true,unh:false,band:false,norm:false,col:"level",w:.9,hole:shape==="year"?0:60,mon:shape!=="year",ctr:shape!=="year"});
const AIRST={year:airDefaults("year"),spiral:airDefaults("spiral")};
const PRESETS={shared:{base:"zero",range:"all",scale:"lin",col:"level",who:true,hole:0,mon:false,ctr:false},normal:{base:"normal",nsrc:"month",range:"city",scale:"lin",col:"dev",who:false,hole:0,mon:false,ctr:false},who:{base:"who",range:"all",scale:"lin",col:"level",who:true,hole:0,mon:false,ctr:false}};let VER="shared",syncYear=null;Object.assign(AIRST.year,PRESETS.shared);   /* default: shared scale from zero (Dish, 2026-10-05) */
function fs(v,clip,sc){v=Math.max(0,Math.min(v,clip));return sc==="lin"?v/clip:sc==="sqrt"?Math.sqrt(v/clip):Math.log10(1+v)/Math.log10(1+clip)}
function pctl(a,p){const s=a.filter(v=>v!=null&&v>=0).sort((x,y)=>x-y);return s.length?s[Math.min(s.length-1,Math.floor(p*(s.length-1)))]:0}
function everyday(st,k){const d=AIR[k],src=st.shape==="year"?d[st.stat]:d.daily;return pctl(src,.99)}
function clipFor(st,k){if(st.range==="city")return Math.max(20,Math.ceil(everyday(st,k)*1.15/5)*5);if(st.range==="all")return Math.max(40,Math.ceil(Math.max(...Object.keys(AIR).map(q=>everyday(st,q)))*1.15/5)*5);return st.clip}
function airYear(svg,k,st,size){const d=AIR[k],c=size/2,brk=st.breakout&&d.pm>clipFor(st,k),grow=st.brklen==="grow",r0=st.hole*size/440,R=size/2-(st.mon?16:8)-(st.breakout?(grow?62:34):0),clip=clipFor(st,k),w=st.w,INK=cv("--ink"),MAG=cv("--event");
 svg.setAttribute("viewBox",`0 0 ${size} ${size}`);svg.innerHTML="";const calls=[];
 const nb=st.base==="normal",bw=st.base==="who",nm=nb&&st.nsrc==="month",
  nrm=doy=>{if(!nm)return d.normal;const f=doy/365*12-.5,i0=Math.floor(f),t=f-i0,a=d.mnorm[(i0+12)%12],b=d.mnorm[(i0+1)%12];return a+(b-a)*t},rm=r0+(R-r0)*.42,kk=(R-rm)/Math.max(1,clip-d.normal);
 const rot=st.top?-(d.ev[3][0]/365)*2*Math.PI:0,ang=doy=>-Math.PI/2+doy/365*2*Math.PI+rot,
  rad=v=>nb?Math.max(r0,Math.min(R,rm+(Math.min(v,clip)-d.normal)*kk)):r0+(R-r0)*fs(v,clip,st.scale),bas=nb?rm:bw?r0+(R-r0)*fs(15,clip,st.scale):r0,baseAt=doy=>bas,radV=(v,doy)=>nm?Math.max(r0,Math.min(R,rm+(Math.min(v,clip)-nrm(doy))*kk)):rad(v),P=(r,a)=>[c+r*Math.cos(a),c+r*Math.sin(a)];
 if(st.band)BANDS.forEach(([a,b,col])=>{if(a>=clip)return;const r1=rad(a),r2=rad(Math.min(b,clip));E("path",{d:`M${c-r2},${c}A${r2},${r2} 0 1 0 ${c+r2},${c}A${r2},${r2} 0 1 0 ${c-r2},${c}M${c-r1},${c}A${r1},${r1} 0 1 1 ${c+r1},${c}A${r1},${r1} 0 1 1 ${c-r1},${c}Z`,fill:col,"fill-opacity":.45,"fill-rule":"evenodd"},svg)});
 const raw=d[st.stat],pts=[];
 if(st.res==="week"){for(let wv=0;wv<52;wv++){const a=[],nn=[];for(let q=wv*7;q<Math.min(365,wv*7+7);q++)if(raw[q]!=null){a.push(raw[q]);nn.push(d.n[q])}if(a.length)pts.push({doy:wv*7+3,v:a.reduce((x,y)=>x+y,0)/a.length,n:nn.reduce((x,y)=>x+y,0)/nn.length})}}
 else raw.forEach((v,doy)=>{if(v!=null)pts.push({doy,v,n:d.n[doy]})});
 const wk=st.res==="week"?3:1;
 if(st.fill&&st.mark==="line"&&pts.length){let fp="";pts.forEach(({doy,v},i)=>{const [x,y]=P(rad(v),ang(doy));fp+=(i?"L":"M")+x.toFixed(1)+","+y.toFixed(1)});E("path",{d:fp+"Z",fill:INK,"fill-opacity":.13,stroke:"none"},svg);E("circle",{cx:c,cy:c,r:bas,fill:cv("--ground-2")},svg)}
 const colOf=(v,doy)=>{if(st.mark==="flat")return flatCol(v);let col=INK;if(st.col==="cat")col=catCol(v);if(st.col==="level")col=flatCol(v);if(st.col==="dev"){const ref=nb?nrm(doy):bw?15:d.normal;col=v>35.5?MAG:v>ref?cv("--cp-mid"):cv("--cp-norm")}if(st.mark==="dot"&&v>=35.5&&st.col!=="cat"&&st.col!=="level")col=MAG;return col};
 pts.forEach(({doy,v,n})=>{const a=ang(doy);let col=INK,op=.8;if(st.col==="cat")col=catCol(v);if(st.col==="level")col=flatCol(v);if(st.col==="dev"){const ref=nb?nrm(doy):bw?15:d.normal;col=v>35.5?MAG:v>ref?cv("--cp-mid"):cv("--cp-norm")}if(st.col==="cov")op=.15+.85*n/7;if(st.mark==="dot"&&v>=35.5&&st.col!=="cat"&&st.col!=="level")col=MAG;
  if(st.mark==="flat"){const [x,y]=P(r0+(R-r0)*.35,a);E("circle",{cx:x,cy:y,r:(1.2*wk*.8+.5)*st.ds,fill:flatCol(v),"fill-opacity":st.col==="cov"?op:1},svg);return}
  if(st.mark==="dot"){const [x,y]=P(rad(v),a);E("circle",{cx:x,cy:y,r:(1.3*w*wk*.8+.4)*st.ds,fill:col,"fill-opacity":op},svg)}
  else{const [x0,y0]=P(baseAt(doy),a),[x1,y1]=P(radV(v,doy),a);E("line",{x1:x0,y1:y0,x2:x1,y2:y1,stroke:col,"stroke-width":w*wk,"stroke-opacity":(nb&&v<nrm(doy))||(bw&&v<15)?op*.55:op},svg)}});
 if(r0>=1)E("circle",{cx:c,cy:c,r:r0,fill:"none",stroke:INK,"stroke-width":1},svg);
 if(bw){E("circle",{cx:c,cy:c,r:bas,fill:"none",stroke:INK,"stroke-width":1.4},svg);calls.push({r:bas,text:"WHO 15 · lines start here",col:INK,da:"0"})}
 if(nb&&!nm){E("circle",{cx:c,cy:c,r:rm,fill:"none",stroke:INK,"stroke-width":1.4},svg);calls.push({r:rm,text:"normal "+Math.round(d.normal)+" · "+["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][d.ev_start[1]]+" normal, all year",col:INK,da:"0"})}
 if(nm){E("circle",{cx:c,cy:c,r:rm,fill:"none",stroke:INK,"stroke-width":1.6},svg);calls.push({r:rm,text:"normal for that time of year",col:INK,da:"0"})}
 const ring=(v,col,da,lab)=>{if(st.mark==="flat")return;if(v>clip){const r=R+5;E("circle",{cx:c,cy:c,r,fill:"none",stroke:col,"stroke-width":1,"stroke-dasharray":da,"stroke-opacity":.6},svg);calls.push({r,text:lab+" · above this scale",col,da});return}const r=rad(v);E("circle",{cx:c,cy:c,r,fill:"none",stroke:col,"stroke-width":1,"stroke-dasharray":da},svg);calls.push({r,text:lab,col,da})};
 if(st.who&&!bw)ring(15,cv("--ink-2"),"1 3","WHO 15");if(st.epa)ring(35.5,MAG,"4 3","EPA 35.5");if(st.unh)ring(55.5,MAG,"8 3","55.5");if(st.norm)ring(d.normal,INK,"0","normal "+Math.round(d.normal));
 const v=d.pm;
 if(st.ev!=="off"&&st.mark==="flat")d.ev.forEach(([doy])=>{const [x,y]=P(r0+(R-r0)*.5,ang(doy));E("circle",{cx:x,cy:y,r:3.2*Math.max(1,st.ds*.8),fill:flatCol(v),stroke:MAG,"stroke-width":1.4},svg)});
 if(st.ev==="spikes"&&st.mark==="dot")d.ev.forEach(([doy])=>{const [x,y]=P(rad(v),ang(doy));E("circle",{cx:x,cy:y,r:3.4*Math.max(1,st.ds*.8),fill:MAG,stroke:cv("--ground-2"),"stroke-width":1},svg)});
 if(st.ev==="spikes"&&st.mark==="line"){const maxOver=Math.max(...Object.values(AIR).map(q=>q.pm))/clip,tipR=brk?(grow?R+12+46*Math.log(v/clip)/Math.log(Math.max(1.5,maxOver)):R+26):0;
  d.ev.forEach(([doy])=>{const a=ang(doy),tip=brk?tipR:radV(v,doy),[x0,y0]=P(baseAt(doy),a),[x1,y1]=P(tip,a);E("line",{x1:x0,y1:y0,x2:x1,y2:y1,stroke:MAG,"stroke-width":Math.max(2,w*2.4),"stroke-linecap":"round"},svg);if(v>clip&&!brk)E("circle",{cx:x1,cy:y1,r:3,fill:MAG},svg)});
  if(brk){const a=ang(d.ev[3][0]),tx=(r,da)=>P(r,a+da);[R+8,R+13].forEach(r=>{const [x0,y0]=tx(r,-.07),[x1,y1]=tx(r,.07);E("line",{x1:x0,y1:y0,x2:x1,y2:y1,stroke:cv("--ground-2"),"stroke-width":3},svg);E("line",{x1:x0,y1:y0,x2:x1,y2:y1,stroke:MAG,"stroke-width":1.2},svg)});
}}
 if(st.ev==="needle"&&st.mark!=="flat"){const a=ang(d.ev[3][0]),[x0,y0]=P(baseAt(d.ev[3][0]),a),[x1,y1]=P(rad(v),a);E("line",{x1:x0,y1:y0,x2:x1,y2:y1,stroke:MAG,"stroke-width":3.5,"stroke-linecap":"round"},svg);E("circle",{cx:x1,cy:y1,r:5,fill:MAG},svg)}
 if(st.mon)"JFMAMJJASOND".split("").forEach((m,i)=>{const [x,y]=P(R+9,ang((i+.5)/12*365));T(svg,{x,y:y+3.5,"text-anchor":"middle","font-size":10,fill:cv("--ink-2"),"font-family":"Jost,sans-serif"},m)});
 centre(svg,c,d,r0,size);
 /* key + hover readout live in the fixed corner box (#hud) */
 HUD.key=calls.sort((a,b)=>b.r-a.r).map(q=>`<details><summary><svg width="16" height="16" aria-hidden="true"><circle cx="8" cy="8" r="6" fill="none" stroke="${q.col}" stroke-width="1.6" stroke-dasharray="${q.da==="0"?"":q.da}"/></svg>${q.text}</summary><p>${keyDesc(q.text,d)}</p>${keyHow(q.text)?`<p class="how">${keyHow(q.text)}</p>`:""}</details>`).join("");HUD.render();
 const NAMES={med:"median",mean:"average",p90:"90th percentile",max:"highest"},MN=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
 const hl=E("line",{stroke:cv("--ink"),"stroke-width":2.2,"stroke-opacity":0,"pointer-events":"none"},svg);
 const evDoys=d.ev.map(e=>e[0]),hit=E("circle",{cx:c,cy:c,r:size/2,fill:"transparent"},svg);
 const onMove=e=>{const m=svg.getScreenCTM();if(!m)return;const p=new DOMPoint(e.clientX,e.clientY).matrixTransform(m.inverse());let a=Math.atan2(p.y-c,p.x-c)+Math.PI/2-rot;a=((a%(2*Math.PI))+2*Math.PI)%(2*Math.PI);const doy=Math.round(a/(2*Math.PI)*365)%365;
  const dt=new Date(Date.UTC(2023,0,1)+doy*864e5),lab=MN[dt.getUTCMonth()]+" "+dt.getUTCDate();
  if(st.ev!=="off"&&evDoys.some(q=>Math.abs(q-doy)<=1)){HUD.set("Worst week · "+d.dates,"µg/m³ · "+(v/35.5).toFixed(1)+"× EPA · "+d.ratio.toFixed(1)+"× normal",String(Math.round(v)),MAG);hl.setAttribute("stroke-opacity",0);return}
  let best=null;pts.forEach(q=>{if(!best||Math.abs(q.doy-doy)<Math.abs(best.doy-doy))best=q});if(!best)return;
  HUD.set(AIR[k].name+" · "+(st.res==="week"?"week of "+lab:lab)+" · "+NAMES[st.stat]+", 2019–2025",("µg/m³"+(nb?" · normal "+nrm(best.doy).toFixed(1):"")+(best.v>35.5?" · above EPA":best.v>15?" · above WHO":"")),best.v.toFixed(1),colOf(best.v,best.doy));
  const aa=ang(best.doy),[x0,y0]=P(baseAt(best.doy),aa),[x1,y1]=P(radV(best.v,best.doy),aa);hl.setAttribute("x1",x0);hl.setAttribute("y1",y0);hl.setAttribute("x2",x1);hl.setAttribute("y2",y1);hl.setAttribute("stroke-opacity",.9)};
 hit.addEventListener("pointermove",onMove);hit.addEventListener("pointerdown",onMove);
 hit.addEventListener("pointerleave",()=>{HUD.set("","");hl.setAttribute("stroke-opacity",0)})}
function centre(svg,c,d,r0,size){if(!(AIRST.year.ctr)||r0<24)return;T(svg,{x:c,y:c-4,"text-anchor":"middle","font-size":21,fill:cv("--event"),"font-family":"Libre Caslon Text,Georgia,serif","font-weight":700},Math.round(d.pm));
 T(svg,{x:c,y:c+10,"text-anchor":"middle","font-size":9.5,fill:cv("--ink"),"font-family":"Jost,sans-serif"},"µg/m³ worst wk");T(svg,{x:c,y:c+24,"text-anchor":"middle","font-size":11.5,fill:cv("--ink"),"font-family":"IBM Plex Mono,monospace"},d.ratio.toFixed(1)+"× normal")}
function airSpiral(svg,k,st,size){const d=AIR[k],c=size/2,INK=cv("--ink"),MAG=cv("--event"),clip=clipFor(st,k),w=st.w,hk=st.h;
 svg.setAttribute("viewBox",`0 0 ${size} ${size}`);svg.innerHTML="";
 const D0=Date.UTC(2019,0,1),n=d.daily.length,years=new Date(D0+(n-1)*864e5).getUTCFullYear()-2018,r0=st.hole*size/440*.7,R=size/2-(st.mon?18:8);
 const gap=(R-r0)/(years+.6),evI=Math.round((Date.UTC(...d.ev_start)-D0)/864e5);
 const doyAt=i=>{const t=new Date(D0+i*864e5);return (t-Date.UTC(t.getUTCFullYear(),0,1))/864e5},yAt=i=>new Date(D0+i*864e5).getUTCFullYear()-2019;
 const rot=st.top?-(doyAt(evI+3)/365)*2*Math.PI:0,ang=i=>-Math.PI/2+doyAt(i)/365*2*Math.PI+rot,base=i=>r0+gap*(yAt(i)+doyAt(i)/365),P=(r,a)=>[c+r*Math.cos(a),c+r*Math.sin(a)],H=v=>gap*1.6*hk*fs(v,clip,st.scale);
 let pth="";for(let i=0;i<n;i+=3){const [x,y]=P(base(i),ang(i));pth+=(i?"L":"M")+x.toFixed(1)+","+y.toFixed(1)}E("path",{d:pth,fill:"none",stroke:INK,"stroke-width":.6,"stroke-opacity":.45},svg);
 if(st.epa&&st.mark!=="flat"){let q="";for(let i=0;i<n;i+=3){const [x,y]=P(base(i)+H(35.5),ang(i));q+=(i?"L":"M")+x.toFixed(1)+","+y.toFixed(1)}E("path",{d:q,fill:"none",stroke:MAG,"stroke-width":.7,"stroke-dasharray":"3 3","stroke-opacity":.7},svg)}
 const items=[];
 if(st.res==="week"){const evB=Math.floor((evI+1)/7),bins={};d.daily.forEach((v,i)=>{if(v<0)return;const b=Math.floor((i+1)/7);(bins[b]=bins[b]||[]).push(v)});
  Object.entries(bins).forEach(([b,a])=>{if(a.length<3)return;b=+b;items.push({i:Math.min(n-1,Math.max(0,b*7+2)),v:b===evB?d.pm:a.reduce((x,y)=>x+y,0)/a.length,ev:b===evB})})}
 else d.daily.forEach((v,i)=>{const ev=i>=evI&&i<evI+7;if(ev)items.push({i,v:d.pm,ev});else if(v>=0)items.push({i,v,ev})});
 const Rmax=base(n-1),wk=st.res==="week"?2.4:1;
 items.forEach(({i,v,ev})=>{const a=ang(i),b=base(i),dens=st.even?Math.max(.22,b/Rmax):1;
  if(st.mark==="flat"){const [x,y]=P(b,a);E("circle",{cx:x,cy:y,r:((ev?2.4:1.3)*wk*.8*dens+.35)*st.ds,fill:ev?MAG:flatCol(v),stroke:ev?cv("--ground-2"):"none","stroke-width":ev?.8:0},svg);return}
  let col=INK,op=.75;if(st.col==="cat")col=catCol(v);if(st.col==="level")col=flatCol(v);if(v>=35.5&&st.col==="ink"){col=MAG;op=.95}if(ev){col=MAG;op=1}
  if(st.mark==="dot"){const [x,y]=P(b+H(v),a);E("circle",{cx:x,cy:y,r:((ev?2.6:1.5)*w*wk*.7*dens+.3)*st.ds,fill:col,"fill-opacity":op},svg)}
  else{const [x0,y0]=P(b,a),[x1,y1]=P(b+H(v),a);E("line",{x1:x0,y1:y0,x2:x1,y2:y1,stroke:col,"stroke-width":(ev?Math.max(2,w*2.4):w*.8*wk)*dens,"stroke-opacity":op},svg)}});
 [0,years-1].forEach(y=>{const i=Math.min(n-1,Math.round(y*365.25)),[x,yy]=P(base(i)-3,ang(i));T(svg,{x:x+3,y:yy+2.5,"font-size":7.5,fill:cv("--ink-2"),"font-family":"IBM Plex Mono,monospace","fill-opacity":.85},String(2019+y))});
 if(st.mon)"JFMAMJJASOND".split("").forEach((m,i)=>{const a=-Math.PI/2+(i+.5)/12*2*Math.PI+rot,[x,y]=P(R+10,a);T(svg,{x,y:y+3.5,"text-anchor":"middle","font-size":10,fill:cv("--ink-2"),"font-family":"Jost,sans-serif"},m)});
 if(st.ctr&&r0>18){T(svg,{x:c,y:c+2,"text-anchor":"middle","font-size":16,fill:MAG,"font-family":"Libre Caslon Text,Georgia,serif","font-weight":700},Math.round(d.pm));T(svg,{x:c,y:c+14,"text-anchor":"middle","font-size":8.5,fill:INK,"font-family":"Jost,sans-serif"},d.ratio.toFixed(1)+"× normal")}}

/* ================= talk disk ================= */
const TALKSPEC=[
 {type:"head",label:"Data"},{type:"seg",key:"grp",label:"Groups",opts:[["3","3 groups"],["4","4 groups"]]},{type:"seg",key:"cnt",label:"Count",opts:[["est","Estimated full week"],["read","Comments read"]]},{type:"tog",key:"big",label:"Leave out biggest thread"},
 {type:"head",label:"Layout"},{type:"seg",key:"al",label:"Groups sit on",opts:[["line","The lines"],["space","The spaces"]]},{type:"tog",key:"txt",label:"Filler text"},{type:"tog",key:"lab",label:"Labels"},{type:"tog",key:"pct",label:"Percentages"},
 {type:"head",label:"Lines"},{type:"sl",key:"n",label:"Layers / ×",min:.25,max:6,step:.25},{type:"sl",key:"op",label:"Intensity",min:10,max:100,step:5},{type:"sl",key:"w",label:"Weight",min:.3,max:2,step:.1},{type:"sl",key:"sp",label:"Spacing",min:.4,max:3,step:.1},{type:"sl",key:"tw",label:"Twist",min:0,max:40,step:1},{type:"sl",key:"dr",label:"Drift",min:0,max:40,step:1},
 {type:"head",label:"Shape"},{type:"sl",key:"pi",label:"Pinch",min:.1,max:.9,step:.05},{type:"sl",key:"stc",label:"Stretch",min:.6,max:1.6,step:.05},
 {type:"head",label:"Colour and extras"},{type:"seg",key:"col",label:"Colour",opts:[["ink","Ink"],["fade","Ink → magenta"],["group","By group"]]},{type:"tog",key:"fill",label:"Fill last shape"},{type:"tog",key:"base",label:"Normal ring"},{type:"tog",key:"tint",label:"Tint sections"}];
const TST={grp:"3",cnt:"est",big:false,al:"line",txt:false,lab:true,pct:true,n:1,op:60,w:.7,sp:1,tw:14,dr:18,pi:.42,stc:1.05,col:"ink",fill:false,base:true,tint:false};
const FILL=["Filler: a line about what people said in this group, two lines at most.","Filler: example of the kind of comment that lands here.","Filler: short summary sentence for this section.","Filler: placeholder for a paraphrased post."];
function talkCounts(k){const t=TALK[k],src=t[TST.cnt],out={};["A","J","E","N"].forEach(g=>{let v=src[g];if(TST.big){const bg=TST.cnt==="est"||!t.sampled?t.big[g]:(t.est[g]?t.big[g]*t.read[g]/t.est[g]:0);v=Math.max(0,v-bg)}out[g]=v});
 return TST.grp==="3"?{names:["Alarm","Adjusting","Living with it"],cols:[cv("--t-alarm"),cv("--t-adjust"),cv("--t-endure")],v:[out.A,out.J,out.E+out.N]}:{names:["Alarm","Adjusting","Enduring","Normalizing"],cols:[cv("--t-alarm"),cv("--t-adjust"),cv("--t-endure"),cv("--t-norm")],v:[out.A,out.J,out.E,out.N]}}
function mix(a,b,f){const h=x=>[1,3,5].map(i=>parseInt(x.slice(i,i+2),16));const A=h(a),B=h(b);return"#"+A.map((x,i)=>Math.round(x+(B[i]-x)*f).toString(16).padStart(2,"0")).join("")}
function blob(c,rs,an,pinch){const Pp=[],n=rs.length,pt=(r,a)=>[c+r*Math.cos(a),c+r*Math.sin(a)];for(let i=0;i<n;i++){const j=(i+1)%n,am=an[i]+((an[j]-an[i]+4*Math.PI)%(2*Math.PI))/2;Pp.push(pt(rs[i],an[i]));Pp.push(pt(Math.min(rs[i],rs[j])*pinch+6,am))}
 const m=Pp.length;let d=`M${Pp[0][0].toFixed(1)},${Pp[0][1].toFixed(1)}`;for(let i=0;i<m;i++){const p0=Pp[(i-1+m)%m],p1=Pp[i],p2=Pp[(i+1)%m],p3=Pp[(i+2)%m];d+=` C${(p1[0]+(p2[0]-p0[0])/6).toFixed(1)},${(p1[1]+(p2[1]-p0[1])/6).toFixed(1)} ${(p2[0]-(p3[0]-p1[0])/6).toFixed(1)},${(p2[1]-(p3[1]-p1[1])/6).toFixed(1)} ${p2[0].toFixed(1)},${p2[1].toFixed(1)}`}return d+"Z"}
function talkDisk(svg,k){const s=svg;s.setAttribute("viewBox","0 0 440 440");s.innerHTML="";const c=220,R=128,G=talkCounts(k),t=G.v.reduce((a,b)=>a+b,0),sh=G.v.map(x=>t?x/t:0),n=sh.length,INK=cv("--ink"),MAG=cv("--event"),pt=(r,a)=>[c+r*Math.cos(a),c+r*Math.sin(a)];
 const step=2*Math.PI/n,an=[...Array(n)].map((_,i)=>-Math.PI/2+i*step),divs=TST.al==="space"?an.map(a=>a-step/2):an;
 if(TST.tint)an.forEach((a,i)=>{const r=R+60,[x0,y0]=pt(r,a-step/2),[x1,y1]=pt(r,a+step/2);E("path",{d:`M${c},${c}L${x0},${y0}A${r},${r} 0 0 1 ${x1},${y1}Z`,fill:G.cols[i],"fill-opacity":.12},s)});
 if(TST.base)E("circle",{cx:c,cy:c,r:R*.62,fill:"none",stroke:INK,"stroke-width":.8,"stroke-dasharray":"2 3"},s);
 divs.forEach(a=>{const [x,y]=pt(R+58,a);E("line",{x1:c,y1:c,x2:x,y2:y,stroke:INK,"stroke-width":.8},s)});
 if(TST.txt)an.forEach((a,i)=>{const [x,y]=pt(R*.98,a+(TST.al==="line"?step/2:0));const words=FILL[i%4].split(" ");let lines=[],cur="";words.forEach(wd=>{if((cur+" "+wd).length>18){lines.push(cur);cur=wd}else cur=cur?cur+" "+wd:wd});lines.push(cur);lines.forEach((ln,q)=>T(s,{x,y:y+(q-lines.length/2)*12+8,"text-anchor":"middle","font-size":9.5,fill:INK,"fill-opacity":.8,"font-style":"italic","font-family":"Jost,sans-serif"},ln))});
 const L=Math.max(1,Math.round(TALK[k].rise*TST.n)),op=TST.op/100,tgt=sh.map(x=>R*(.18+TST.stc*x));let lx=0,ly=0;sh.forEach((x,i)=>{lx+=x*Math.cos(an[i]);ly+=x*Math.sin(an[i])});const dom=sh.indexOf(Math.max(...sh));
 for(let q=0;q<=L;q++){const f=Math.pow(q/L,TST.sp),e=f*f*(3-2*f),rs=tgt.map(b=>R*.16+(b-R*.16)*e),last=q===L;let col=INK;if(TST.col==="fade")col=mix(INK,MAG,e);if(TST.col==="group")col=mix(INK,G.cols[dom],e);if(last)col=MAG;
  E("path",{d:blob(c,rs,an,TST.pi),fill:last&&TST.fill?MAG:"none","fill-opacity":.22,stroke:col,"stroke-width":last?TST.w*2.6:TST.w,"stroke-opacity":last?1:Math.min(1,op*(.3+.7*f)),transform:`translate(${(lx*TST.dr*(1-e)).toFixed(1)},${(ly*TST.dr*(1-e)).toFixed(1)}) rotate(${((1-e)*-TST.tw).toFixed(1)},${c},${c})`},s)}
 an.forEach((a,i)=>{const [x,y]=pt(R+74,a),up=Math.sin(a)<-.5;if(TST.lab)T(s,{x,y:y+(up?-4:8),"text-anchor":"middle","font-size":12.5,fill:G.cols[i],"font-weight":600,"font-family":"Jost,sans-serif"},G.names[i]);if(TST.pct)T(s,{x,y:y+(up?10:22),"text-anchor":"middle","font-size":12,fill:INK,"font-family":"IBM Plex Mono,monospace"},Math.round(sh[i]*100)+"%")});
 T(s,{x:12,y:428,"font-size":20,fill:INK,"font-family":"Libre Caslon Text,Georgia,serif","font-weight":700},TALK[k].rise.toFixed(1)+"×");T(s,{x:58,y:427,"font-size":10.5,fill:INK,"font-family":"Jost,sans-serif"},`more air talk than normal · ${L} layers · ${Math.round(t)} comments`+(TST.big?" (biggest thread left out)":""))}

/* ================= corner box (hover readout + key) ================= */
function keyHow(t){if(t.startsWith("normal"))return "How: average each week of that month, 2019–25, then take the middle one.";return ""}
function keyDesc(t,d){const off=t.includes("above this scale")?" Off this scale.":"";
 if(t.startsWith("EPA 35.5"))return "U.S. daily limit. Above it, air is unhealthy."+off;
 if(t.startsWith("WHO 15 · lines"))return "Out = dirtier than WHO 15. In = cleaner.";
 if(t.startsWith("WHO 15"))return "WHO's daily guideline. Stricter than the EPA's."+off;
 if(t.startsWith("55.5"))return "EPA 'Unhealthy' level: everyone may feel it."+off;
 if(t.startsWith("normal for that time"))return "A usual week for that month. Lines show the gap.";
 if(t.startsWith("normal"))return "Usual level for the worst week's month, all year."+off;
 return ""}
const HUD={key:"",l1:"",l2:"",num:"",col:"",vis:false,
 set(a,b,num,col){this.l1=a;this.l2=b;this.num=num||"";this.col=col||"";this.render()},
 render(){const h=document.getElementById("hud");if(!h)return;document.getElementById("hud1").textContent=this.l1||"";const h2=document.getElementById("hud2");h2.textContent="";if(this.num){const bd=document.createElement("span");bd.className="badge";bd.style.background=this.col;bd.textContent=this.num;h2.appendChild(bd)}if(this.l2){const tx=document.createElement("span");tx.textContent=this.l2;h2.appendChild(tx)}
  if(!this.l1){document.getElementById("hud1").innerHTML='<span class="hint">Hover or tap a line on the air disk for its value</span>'}
  const hk=document.getElementById("hudkey");if(hk.dataset.k!==this.key){const open=[...hk.querySelectorAll("details")].map(x=>x.open);hk.innerHTML=this.key;hk.dataset.k=this.key;hk.querySelectorAll("details").forEach((x,i)=>{if(open[i])x.open=true})}hk.hidden=!this.key}};
let hudIO=null;
function watchHud(){if(hudIO)hudIO.disconnect();const el=document.getElementById("p-air");if(!el)return;hudIO=new IntersectionObserver(es=>{es.forEach(e=>{HUD.vis=e.isIntersecting});HUD.render()},{threshold:.15});hudIO.observe(el)}
/* ================= panel ================= */
function timeline(svg,k){const d=AIR[k],W=Math.max(320,svg.parentElement.clientWidth),H=86,L=6,R=6,n=d.daily.length,x=i=>L+(W-L-R)*i/(n-1),D0=Date.UTC(2019,0,1),evI=Math.round((Date.UTC(...d.ev_start)-D0)/864e5);
 svg.setAttribute("viewBox",`0 0 ${W} ${H}`);svg.innerHTML="";const INK=cv("--ink"),MAG=cv("--event");
 E("rect",{x:x(evI)-3,y:6,width:Math.max(6,x(evI+7)-x(evI))+6,height:52,fill:MAG,"fill-opacity":.14},svg);
 d.daily.forEach((v,i)=>{if(v<0)E("line",{x1:x(i),x2:x(i),y1:52,y2:58,stroke:cv("--rule"),"stroke-width":1},svg)});
 E("line",{x1:L,x2:W-R,y1:58,y2:58,stroke:INK,"stroke-width":1},svg);
 let cnt=0;d.daily.forEach((v,i)=>{if(v>35.5&&!(i>=evI&&i<evI+7)){cnt++;E("line",{x1:x(i),x2:x(i),y1:12,y2:58,stroke:MAG,"stroke-width":1.3,"stroke-opacity":.85},svg)}});
 for(let i=evI;i<evI+7;i++)E("line",{x1:x(i),x2:x(i),y1:6,y2:58,stroke:MAG,"stroke-width":2.2},svg);
 const yrs=new Date(D0+(n-1)*864e5).getUTCFullYear();for(let y=2019;y<=yrs;y++){const i=Math.round((Date.UTC(y,0,1)-D0)/864e5);E("line",{x1:x(i),x2:x(i),y1:58,y2:63,stroke:INK},svg);T(svg,{x:x(i)+2,y:75,"font-size":10.5,fill:cv("--ink-2"),"font-family":"IBM Plex Mono,monospace"},String(y))}
 T(svg,{x:Math.min(W-R-4,x(evI)+8),y:16,"font-size":10.5,fill:cv("--event-ink"),"font-family":"Jost,sans-serif","font-weight":600,"text-anchor":x(evI)>W*.7?"end":"start","dx":x(evI)>W*.7?-14:0},"worst week");
 return cnt}
function stateOutline(svg,k){const c=CITIES[k],f=STATES.features.find(q=>q.properties.n===c.st),pj=d3.geoMercator().fitExtent([[6,6],[126,126]],f),pp=d3.geoPath(pj);svg.setAttribute("viewBox","0 0 132 132");svg.innerHTML="";
 E("path",{d:pp(f),fill:cv("--ground"),stroke:cv("--ink"),"stroke-width":1.4,"stroke-linejoin":"round"},svg);const [x,y]=pj([c.lon,c.lat]);E("circle",{cx:x,cy:y,r:7,fill:"none",stroke:cv("--event"),"stroke-width":1.5},svg);E("circle",{cx:x,cy:y,r:3.6,fill:cv("--event")},svg);
 T(svg,{x:66,y:130,"text-anchor":"middle","font-size":10,fill:cv("--ink-2"),"font-family":"Jost,sans-serif","letter-spacing":".1em"},(STNAME[c.st]||c.st).toUpperCase())}
function airDetail(k){const d=AIR[k],D0=Date.UTC(2019,0,1),end=Math.round((Date.UTC(2026,0,1)-D0)/864e5);let bad=0,meas=0;d.daily.forEach((v,i)=>{if(i<end&&v>=0){meas++;if(v>35.5)bad++}});
 return `<div class="g"><div><div class="k">Worst week</div><div class="n">${Math.round(d.pm)}</div><div class="k">µg/m³ · ${d.dates}</div></div><div><div class="k">Normal for that month</div><div class="n">${d.normal.toFixed(0)}</div></div><div><div class="k">How unusual</div><div class="n">${d.ratio.toFixed(1)}×</div></div><div><div class="k">Days above EPA 35.5</div><div class="n">${bad}</div><div class="k">of ${meas.toLocaleString()} measured, 2019–2025</div></div></div>
 <p style="margin:0">${d.cause}. ${d.ratio<4?"The worst week sat close to what the city already lives with: <b>harmful, but familiar</b>.":"The worst week came out of a much cleaner normal: <b>harmful and out of place</b>."}</p><p class="cap">Daily averages from reference monitors (OpenAQ). Grey/ink marks leave out the worst week; the worst week is drawn at its weekly average.</p>`}
function talkDetail(k){const G=talkCounts(k),t=G.v.reduce((a,b)=>a+b,0),p=v=>t?Math.round(100*v/t)+"%":"–",dom=G.names[G.v.indexOf(Math.max(...G.v))];
 return `<div class="g"><div><div class="k">Air talk vs normal</div><div class="n">${TALK[k].rise.toFixed(1)}×</div></div>${G.names.map((nm,i)=>`<div><div class="k">${nm}</div><div class="n">${p(G.v[i])}</div></div>`).join("")}</div>
 <p style="margin:0">In its worst week, ${AIR[k].name}'s subreddit talked about the air ${TALK[k].rise.toFixed(1)}× more than in a normal week. The largest share of that talk was <b>${dom.toLowerCase()}</b>.</p>
 <p class="cap">Groups are Claude's draft sorting, not yet checked by a person.${TALK[k].sampled?" A random 400 comments were read and weighted up to the full week.":""} ${Math.round(t)} air comments ${TST.big?"(biggest thread left out)":""}.</p>`}

function drawPanel(){if(!current)return;const k=current;const cnt=timeline(document.getElementById("p-tl"),k);
 document.getElementById("p-tlcap").textContent=`Each magenta line is a day above the EPA's 35.5 µg/m³ line (${cnt} days outside the worst week); the shaded band is the worst week. Grey ticks under the axis are days with no reading.`;
 stateOutline(document.getElementById("p-state"),k);airYear(document.getElementById("p-air"),k,AIRST.year,440);
 if(!document.getElementById("p-spwrap").hidden)airSpiral(document.getElementById("p-sp"),k,AIRST.spiral,440);
 talkDisk(document.getElementById("p-talk"),k);document.getElementById("p-airdet").innerHTML=airDetail(k);document.getElementById("p-talkdet").innerHTML=talkDetail(k)}

/* ---------- open / close, pulsing rings on Bidisha's map, and the hairline from dot to panel ---------- */
function openCity(k){current=k;const pan=document.getElementById("cp-panel"),d=AIR[k],c=CITIES[k];pan.hidden=false;document.getElementById("cp-hint").hidden=true;
 pan.innerHTML=`<div class="cp-sec"><div class="cp-ph"><span>Analysed period · PM2.5 above the EPA line</span><button class="cp-x" id="px">Close</button></div><div class="cp-tl"><svg id="p-tl" role="img" aria-label="Timeline of days above the EPA line"></svg></div><p class="cp-cap" id="p-tlcap"></p></div>
 <div class="cp-sec"><div class="cp-head"><svg id="p-state" role="img" aria-label="${c.st} outline with ${c.name}"></svg><div><h3 class="cp-cname">${c.name}<span>${c.st}</span></h3><div class="cp-sub">Worst week ${d.dates} · ${d.cause}</div>
  <dl class="cp-char"><dt>Economy</dt><dd class="cp-filler">${CHAR.economy}</dd><dt>Politics</dt><dd class="cp-filler">${CHAR.politics}</dd><dt>People</dt><dd class="cp-filler">${CHAR.people}</dd></dl></div></div></div>
 <div class="cp-disks">
 <div class="cp-sec cp-disk"><h4>The air</h4><p class="cp-ds">A typical year: one line per day, with the worst week on top. Click the disk for details.</p>
  <div class="cp-ctl" style="padding:0"><div class="crow"><span class="cl">Compare views</span><div class="seg" id="p-ver"><button type="button" data-v="shared">Shared scale · from zero</button><button type="button" data-v="normal">Lines from the city's normal (inverted)</button><button type="button" data-v="who">Lines from WHO 15 (inverted)</button></div></div>
   <div class="crow" id="p-nrow" hidden><span class="cl">Which normal</span><div class="seg" id="p-nsrc"><button type="button" data-v="study">Worst week's month (one number all year)</button><button type="button" data-v="month">Each month's own</button></div></div></div>
  <div class="cp-airwrap"><div id="hud" aria-live="polite"><div class="h1" id="hud1"></div><div class="h2" id="hud2"></div><div class="cp-key" id="hudkey"></div></div><svg class="cp-art" id="p-air" role="img" aria-label="Typical-year air disk"></svg></div><div class="cp-det" id="p-airdet" hidden></div>
  <details class="cp-tune"><summary>Tune · typical year</summary><div class="cp-ctl" id="c-year"></div></details>
  <button class="cp-expand" id="p-exp" aria-expanded="false">Expand into the spiral · every year ↓</button>
  <div id="p-spwrap" hidden style="display:grid;gap:8px"><p class="cp-ds">Every week from 2019, one loop per year. Colour shows the level: blue up to WHO 15, orange to EPA 35.5, magenta above.</p><svg class="cp-art" id="p-sp" role="img" aria-label="Spiral air disk"></svg><details class="cp-tune"><summary>Tune · spiral</summary><div class="cp-ctl" id="c-sp"></div></details></div></div>
 <div class="cp-sec cp-disk"><h4>The talk</h4><p class="cp-ds">How the city's subreddit talked about the air in its worst week. Click the disk for details.</p><svg class="cp-art" id="p-talk" role="img" aria-label="Talk disk"></svg><div class="cp-det" id="p-talkdet" hidden></div>
  <details class="cp-tune"><summary>Tune · talk disk</summary><div class="cp-ctl" id="c-talk"></div></details></div>
 </div>`;
 document.getElementById("px").addEventListener("click",closeCity);
 drawPanel();
 const syncY=controls(document.getElementById("c-year"),AIRSPEC,AIRST.year,()=>{drawPanel()});syncYear=syncY;
 const ver=document.getElementById("p-ver"),markVer=()=>ver.querySelectorAll("button").forEach(b=>b.setAttribute("aria-pressed",b.dataset.v===VER));markVer();
 const nrow=document.getElementById("p-nrow"),markN=()=>{nrow.hidden=AIRST.year.base!=="normal";nrow.querySelectorAll("button").forEach(b=>b.setAttribute("aria-pressed",b.dataset.v===AIRST.year.nsrc))};markN();
 nrow.querySelectorAll("button").forEach(b=>b.addEventListener("click",()=>{AIRST.year.nsrc=b.dataset.v;syncYear();markN();drawPanel()}));
 ver.querySelectorAll("button").forEach(b=>b.addEventListener("click",()=>{VER=b.dataset.v;Object.assign(AIRST.year,PRESETS[VER]);syncYear();markVer();markN();drawPanel()}));
 document.getElementById("c-year").addEventListener("click",()=>setTimeout(markN,0));
 controls(document.getElementById("c-sp"),AIRSPEC,AIRST.spiral,()=>{drawPanel()});controls(document.getElementById("c-talk"),TALKSPEC,TST,()=>{drawPanel()});
 document.getElementById("p-air").addEventListener("click",()=>{const e=document.getElementById("p-airdet");e.hidden=!e.hidden;requestAnimationFrame(wire)});
 document.getElementById("p-talk").addEventListener("click",()=>{const e=document.getElementById("p-talkdet");e.hidden=!e.hidden;requestAnimationFrame(wire)});
 document.getElementById("p-exp").addEventListener("click",e=>{const w=document.getElementById("p-spwrap"),open=w.hidden;w.hidden=!open;e.currentTarget.setAttribute("aria-expanded",open);e.currentTarget.textContent=open?"Collapse the spiral ↑":"Expand into the spiral · every year ↓";if(open)drawPanel();requestAnimationFrame(wire)});
 rings();requestAnimationFrame(wire);pan.scrollIntoView({behavior:matchMedia("(prefers-reduced-motion: reduce)").matches?"auto":"smooth",block:"nearest"})}
function closeCity(){current=null;document.getElementById("cp-panel").hidden=true;document.getElementById("cp-hint").hidden=false;rings();wire()}
const MP=d3.geoAlbersUsa().fitExtent([[20,20],[955,590]],STATES);
function rings(){const svg=d3.select("#imap");let g=svg.select("g.cp-rings");if(g.empty())g=svg.append("g").attr("class","cp-rings").attr("pointer-events","none");g.raise();g.selectAll("*").remove();
 Object.entries(CITIES).forEach(([k,c])=>{const p=MP([c.lon,c.lat]);if(!p)return;const r=3+17*Math.sqrt(c.pm/300)+4;
  g.append("circle").attr("class","cp-pulse").attr("cx",p[0]).attr("cy",p[1]).attr("r",r).attr("fill","none").attr("stroke",cv("--event")).attr("stroke-width",2);
  if(k===current)g.append("circle").attr("cx",p[0]).attr("cy",p[1]).attr("r",r+3).attr("fill","none").attr("stroke",cv("--event")).attr("stroke-width",2.5)})}
function wire(){const w=document.getElementById("cp-wire");if(!w)return;w.innerHTML="";const pan=document.getElementById("cp-panel");if(!current||pan.hidden)return;
 const host=w.parentElement.getBoundingClientRect(),dot=document.querySelector(`#imap .mcity[data-slug="${current}"] circle`),hd=document.getElementById("p-state");if(!dot||!hd)return;
 const a=dot.getBoundingClientRect(),b=hd.getBoundingClientRect(),x1=a.left+a.width/2-host.left,y1=a.top+a.height/2-host.top,x2=b.left+b.width/2-host.left,y2=b.top-host.top;
 E("path",{d:`M${x1},${y1} C${x1},${(y1+y2)/2} ${x2},${(y1+y2)/2} ${x2},${y2}`,fill:"none",stroke:cv("--event"),"stroke-width":1.6},w);E("circle",{cx:x2,cy:y2,r:3.5,fill:cv("--event")},w);E("circle",{cx:x1,cy:y1,r:a.width/2+3,fill:"none",stroke:cv("--event"),"stroke-width":1.6},w)}
const mapEl=document.getElementById("imap");
mapEl.addEventListener("click",e=>{const g=e.target.closest(".mcity");if(g&&CITIES[g.dataset.slug])openCity(g.dataset.slug)});
mapEl.addEventListener("keydown",e=>{if(e.key!=="Enter"&&e.key!==" ")return;const g=e.target.closest(".mcity");if(g&&CITIES[g.dataset.slug]){e.preventDefault();openCity(g.dataset.slug)}});
new MutationObserver(()=>{if(!mapEl.querySelector("g.cp-rings")||mapEl.lastElementChild.getAttribute("class")!=="cp-rings")rings()}).observe(mapEl,{childList:true});
addEventListener("scroll",()=>requestAnimationFrame(wire),{passive:true});
new ResizeObserver(()=>{if(current)timeline(document.getElementById("p-tl"),current);wire()}).observe(document.querySelector(".imap-plate"));
rings();
})();
