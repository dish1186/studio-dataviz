// Moved from index.html (snapshot d689e08), line 1573; comments on calculations and sources added 2026-10-07; code unchanged.
// "Same air": Bakersfield vs. Indianapolis, scrubbed by scroll (from the Same Air, Different Normal artifact K2uKZiFc28iTnctQkJN4UT).
// Display only; numbers are typed in from data.js and the tone counts.
(function(){
  const NS="http://www.w3.org/2000/svg";
  const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
  const $=id=>document.getElementById('sa-'+id);   // ids are prefixed sa- inside Boiling Frog
  function el(tag,attrs,parent,text){const e=document.createElementNS(NS,tag);for(const k in attrs)e.setAttribute(k,attrs[k]);parent.appendChild(e);if(text!=null)e.textContent=text;return e}
  // Phone and wide layouts differ, so the story is rebuilt from its starting markup whenever the window crosses 700px.
  const SVG0=$('svg').innerHTML, HEADS0=document.querySelector('.sa .heads').innerHTML, PHONE=matchMedia('(max-width:700px)');
  let built=null, first=true;
  function build(){
  if(built){built.st.kill();built.tl.kill();$('svg').innerHTML=SVG0;document.querySelector('.sa .heads').innerHTML=HEADS0;$('svg').setAttribute('viewBox','0 0 1000 680')}
  $('bak').style.fill='var(--bak)'; $('ind').style.fill='var(--ind)';
  // frame 0: centre the two balls and their captions as one group on the screen (Gina, Oct 6). The balls' later moves
  // are tweens to fixed positions, so only this opening layout shifts.
  { const capR=Math.max(...['cap1','cap2'].map(id=>{const b=$(id).getBBox();return b.x+b.width})), left=+$('bak').getAttribute('x'), dx=Math.round(500-(left+capR)/2);
    if(Math.abs(dx)>2){['bak','ind'].forEach(id=>$(id).setAttribute('x',+$(id).getAttribute('x')+dx)); $('scene1').setAttribute('transform',`translate(${dx},0)`);} }
  // phones: a taller canvas, the chart centred in it, and the two talk disks stacked
  const MOBILE=PHONE.matches, WY=MOBILE?300:0;
  if(MOBILE){$('svg').setAttribute('viewBox','0 0 1000 1300');$('world').setAttribute('transform',`translate(0,${WY})`)}

  /* ---------- lollipop geometry ---------- */
  const BASE=340, CB=400, CI=640, DOT=44;
  const upHarm=v=>BASE-v/55*150;       // 55 µg/m³ -> 150 above the line
  const upNorm=v=>BASE-v/5*210;        // × normal pm2.5, 5× -> 210
  const down=v=>BASE+v/10*290;         // × normal air talk, 10× -> 290
  const gL=$('lolli'), gLab=$('labels');
  const stem=(x)=>el('line',{x1:x,x2:x,y1:BASE,y2:BASE,class:'stem'},gL);
  const stemTB=stem(CB), stemTI=stem(CI), stemDB=stem(CB), stemDI=stem(CI);
  const dB=el('circle',{cx:CB,cy:BASE,r:0},gL), dI=el('circle',{cx:CI,cy:BASE,r:0},gL);
  dB.style.fill=dI.style.fill='var(--talk)';
  const cityB=el('text',{x:CB,y:BASE+38,'text-anchor':'middle',class:'city',opacity:0},gLab,'bakersfield');
  const cityI=el('text',{x:CI,y:BASE+38,'text-anchor':'middle',class:'city',opacity:0},gLab,'indianapolis');
  function pair(x,y,anchor,num,unit){const g=el('g',{opacity:0},gLab);const n=el('text',{x,y:y+4,'text-anchor':anchor,class:'big'},g,num);el('text',{x,y:y+30,'text-anchor':anchor,class:'unit'},g,unit);return {g,n}}
  const LB=CB-DOT/2-16, LI=CI+DOT/2+16;
  const harmB=pair(LB,upHarm(55),'end','55','µg/m³'), harmI=pair(LI,upHarm(55),'start','55','µg/m³');
  const talkB=pair(LB,down(4.8),'end','4.8×','air talk'), talkI=pair(LI,down(9.5),'start','9.5×','air talk');
  const normB=pair(LB,upNorm(2.9),'end','2.9×','vs. normal'), normI=pair(LI,upNorm(4.4),'start','4.4×','vs. normal');
  // colour code (brand.md): harmful numbers orange, air talk indigo, × normal violet
  [harmB,harmI].forEach(q=>q.n.style.fill='var(--harm-ink)'); [talkB,talkI].forEach(q=>q.n.style.fill='var(--react)'); [normB,normI].forEach(q=>q.n.style.fill='var(--unusual-ink)');
  // Indianapolis's 9.5× air-talk ball in the abnormal colour (Gina, Oct 6), so the bigger reaction to the more unusual week stands out
  dI.style.fill='var(--unusual-2)'; talkI.n.style.fill='var(--unusual-2)';
  const base=$('base'); base.style.strokeDasharray='640'; base.style.strokeDashoffset='640';

  /* ---------- talk disks, drawn like the city cards' sentiment disk (Dish's Air Talk Disks recipe: riso colours, grainy
     blended outline, dot screen, hairline spokes, red reacting | living-with-it split). Four groups, corrected counts. ---------- */
  const GROUPS=["alarm","adjusting","enduring","normalizing"], SPK=[-135,135,45,-45].map(d=>d*Math.PI/180);
  // CALCULATION / DATA · DATA, typed in: ratio here is the "× more air talk" (data/pm25.js rise: Bakersfield 4.809 -> 4.8,
  //   Indianapolis 9.529 -> 9.5); cnt = corrected tone counts A, J, E, N (= CORR in js/how-they-talked.js, spectrum_07_corrected/city_shares.csv).
  //   Shown: share = count / total of the four; reacting % = round(100 × (A + J) / total); "~N air posts and comments" = round(total).
  //   Shape only: each lobe reaches R × min(1.08, 0.18 + 1.9 × share); wedge opacity = 0.4 + 0.6 × share / largest share.
  const DATA={bakersfield:{name:"Bakersfield",sub:"dec 2–8, 2024",ratio:4.8,cnt:[13.73,5.45,21.92,9.77]},indianapolis:{name:"Indianapolis",sub:"jun 26–jul 2, 2023",ratio:9.5,cnt:[45.55,19.54,27.19,7.03]}};   // corrected tone counts (alarm, adjusting, enduring, normalizing): data/processed/reddit/spectrum_07_corrected/city_shares.csv
  const DC=220, DR=128, DS=MOBILE?1:.88;
  const RISO=[["#f2643c","#ec4f9a","#8a4fe0","#2a9d9a"],["#ff7a52","#ff6fb0","#a77bff","#3fc4c0"]];
  const hmix=(a,b,t)=>{const h=x=>[1,3,5].map(i=>parseInt(x.slice(i,i+2),16)),A=h(a),B=h(b);return"#"+A.map((x,i)=>Math.round(x+(B[i]-x)*t).toString(16).padStart(2,"0")).join("")};
  const gcol=()=>{const P=RISO[getComputedStyle(document.documentElement).getPropertyValue("--ground").trim().toLowerCase()==="#160d4c"?1:0];
    return [0,1,2,3].map(i=>{const t=(i+.5)/4*(P.length-1),k=Math.min(P.length-2,Math.floor(t));return hmix(P[k],P[k+1],t-k)})};
  const pt=(c,r,a)=>[c+r*Math.cos(a),c+r*Math.sin(a)];
  function blob(c,rs,an,pinch){const Q=[],n=rs.length;for(let i=0;i<n;i++){const j=(i+1)%n,am=an[i]+((an[j]-an[i]+4*Math.PI)%(2*Math.PI))/2;Q.push(pt(c,rs[i],an[i]));Q.push(pt(c,Math.min(rs[i],rs[j])*pinch+5*DR/96,am))}
    const m=Q.length;let d=`M${Q[0][0].toFixed(1)},${Q[0][1].toFixed(1)}`;for(let i=0;i<m;i++){const p0=Q[(i-1+m)%m],p1=Q[i],p2=Q[(i+1)%m],p3=Q[(i+2)%m];d+=` C${(p1[0]+(p2[0]-p0[0])/6).toFixed(1)},${(p1[1]+(p2[1]-p0[1])/6).toFixed(1)} ${(p2[0]-(p3[0]-p1[0])/6).toFixed(1)},${(p2[1]-(p3[1]-p1[1])/6).toFixed(1)} ${p2[0].toFixed(1)},${p2[1].toFixed(1)}`}return d+"Z"}
  function buildDisk(key,cx,cy){
    const d=DATA[key],c=DC,R=DR,k=R/96,RR=R+34*k,t=d.cnt.reduce((a,b)=>a+b,0),sh=d.cnt.map(x=>x/t),mx=Math.max(...sh),GC=gcol(),id="sad"+key;
    const ord=[0,1,2,3].sort((i,j)=>SPK[i]-SPK[j]),pick=a=>ord.map(i=>a[i]),FX={filterUnits:"userSpaceOnUse",x:-80,y:-80,width:c*2+160,height:c*2+160};
    const outer=el('g',{transform:`translate(${cx-c*DS},${cy-c*DS}) scale(${DS})`},$('disks'));
    const defs=el('defs',{},outer),frame=el('g',{opacity:0},outer);
    // dot screen fading to the rim
    const pat=el('pattern',{id:id+"ht",width:9*k,height:9*k,patternUnits:"userSpaceOnUse",x:c,y:c},defs);el('circle',{cx:4.5*k,cy:4.5*k,r:.75*k},pat).style.fill='var(--ink)';
    const rg=el('radialGradient',{id:id+"rf",cx:c,cy:c,r:RR,gradientUnits:"userSpaceOnUse"},defs);[[0,1],[.65,.9],[1,0]].forEach(([o,a])=>el('stop',{offset:o,'stop-color':'#fff','stop-opacity':a},rg));
    const mk=el('mask',{id:id+"hm",maskUnits:"userSpaceOnUse",x:-80,y:-80,width:c*2+160,height:c*2+160},defs);el('circle',{cx:c,cy:c,r:RR,fill:`url(#${id}rf)`},mk);
    el('circle',{cx:c,cy:c,r:RR,fill:`url(#${id}ht)`,opacity:.34,mask:`url(#${id}hm)`},frame);
    // split and spokes
    el('line',{x1:c,x2:c,y1:c-RR-8*k,y2:c+RR+8*k,'stroke-width':1,'stroke-opacity':.7},frame).style.stroke='var(--split, #c8201e)';
    SPK.forEach(a=>{const [xa,ya]=pt(c,R*.22,a),[x,y]=pt(c,R+38*k,a);el('line',{x1:xa,y1:ya,x2:x,y2:y,'stroke-width':.9,'stroke-opacity':.45},frame).style.stroke='var(--ink)'});
    // the shape: one wedge per group, blurred so the hues blend, clipped to the outline and grained; the wedges fade in one by one
    const tgt=sh.map(x=>R*Math.min(1.08,.18+1.9*x)),cp=el('clipPath',{id:id+"c"},defs);el('path',{d:blob(c,pick(tgt),pick(SPK),.42)},cp);
    const gf=el('filter',{id:id+"g",...FX,'color-interpolation-filters':'sRGB'},defs);
    el('feTurbulence',{type:"fractalNoise",baseFrequency:(.95/k).toFixed(3),numOctaves:2,seed:7,result:"nz"},gf);
    el('feColorMatrix',{in:"nz",type:"matrix",values:"0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  1.6 0 0 0 -0.3",result:"na"},gf);
    el('feColorMatrix',{in:"SourceGraphic",type:"matrix",values:"0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0",result:"sa"},gf);
    el('feComposite',{in:"sa",in2:"na",operator:"arithmetic",k1:0,k2:2.4,k3:-1.4,k4:.15,result:"m"},gf);
    el('feComposite',{in:"SourceGraphic",in2:"m",operator:"in"},gf);
    const bf=el('filter',{id:id+"b",...FX},defs);el('feGaussianBlur',{stdDeviation:9*k},bf);
    const gb=el('g',{filter:`url(#${id}b)`},el('g',{'clip-path':`url(#${id}c)`},el('g',{filter:`url(#${id}g)`},outer)));
    const layers=SPK.map((a,i)=>{const r=R+40*k,[x0,y0]=pt(c,r,a-Math.PI/4),[x1,y1]=pt(c,r,a+Math.PI/4);
      const p=el('path',{d:`M${c},${c}L${x0.toFixed(1)},${y0.toFixed(1)}A${r},${r} 0 0 1 ${x1.toFixed(1)},${y1.toFixed(1)}Z`,fill:GC[i],opacity:0},gb);p.dataset.op=(.4+.6*sh[i]/mx).toFixed(3);return p});
    const dot=el('circle',{cx:c,cy:c,r:2.6*k},frame);dot.style.fill='var(--ink)';
    // labels: group names in spaced small caps, shares in italic serif; the two sides named at the top of the split
    const labs=el('g',{opacity:0},outer);
    SPK.forEach((a,i)=>{const [x,y]=pt(c,R+50*k,a),anc=Math.cos(a)>0?'start':'end',y1=Math.sin(a)<0?y-12*k:y+4*k;
      el('text',{x,y:y1,'text-anchor':anc,class:'dlab'},labs,GROUPS[i].toUpperCase());
      el('text',{x,y:y1+17*k,'text-anchor':anc,class:'dpct'},labs,Math.round(sh[i]*100)+'%')});
    const rx=Math.round(100*(sh[0]+sh[1])),yT=c-RR-14*k;
    [["REACTING",rx,'end',-8*k],["LIVING WITH IT",100-rx,'start',8*k]].forEach(([l,v,anc,dx])=>{
      el('text',{x:c+dx,y:yT-15*k,'text-anchor':anc,class:'dlab'},labs,l);el('text',{x:c+dx,y:yT+3*k,'text-anchor':anc,class:'dpct'},labs,v+'%')});
    const head=el('g',{opacity:0},outer);
    el('text',{x:c,y:-74,'text-anchor':'middle',class:'dname'},head,d.name);
    el('text',{x:c,y:-48,'text-anchor':'middle',class:'dsub'},head,d.sub);
    const foot=el('g',{opacity:0},outer);
    el('text',{x:c,y:c*2+40,'text-anchor':'middle',class:'dfoot'},foot,d.ratio+'× more air talk');
    el('text',{x:c,y:c*2+64,'text-anchor':'middle',class:'dfoot-s'},foot,`~${Math.round(t)} air posts and comments`);
    return {frame,layers,labs,head,foot};
  }
  const DPOS=MOBILE?[[500,320],[500,990]]:[[245,330],[755,330]];
  const diskB=buildDisk('bakersfield',...DPOS[0]), diskI=buildDisk('indianapolis',...DPOS[1]);

  /* ---------- "they respond differently": air-talk jump for all nine cities, smallest to largest (from data.js) ---------- */
  const BX0=MOBILE?370:340, BX1=MOBILE?950:870, BY0=MOBILE?60:132, BST=MOBILE?62:52, BH=MOBILE?34:26;
  // CALCULATION · "× more air talk" bars: the nine cities sorted by rise (data/pm25.js); bar length = rise / largest rise; label rounded to 0 decimals at 10× and up, else 1
  const CITIES9=(window.PM25?window.PM25.cities:[]).filter(c=>c.rise!=null).sort((a,b)=>a.rise-b.rise);
  const rmax=Math.max(...CITIES9.map(c=>c.rise),1);
  const bars=CITIES9.map((c,i)=>{const y=BY0+i*BST,w=(BX1-BX0)*c.rise/rmax;
    const g=el('g',{opacity:0},$('bars'));
    el('text',{x:MOBILE?20:150,y:y+BH/2+7,class:'bname'},g,`${c.name}, ${c.state}`);
    const r=el('rect',{x:BX0,y,width:0,height:BH,rx:BH/2.6},g);r.style.fill='var(--ind)';
    const v=el('text',{x:BX0+w-12,y:y+BH/2+6,'text-anchor':'end',class:'bval',opacity:0},g,(c.rise>=10?c.rise.toFixed(0):c.rise.toFixed(1))+'×');
    return {g,r,v,w}});

  /* ---------- "let's take a look at two cities": little state outlines, each with its city dot (US_STATES from states.js) ---------- */
  function drawState(code,box,ll,label){
    const ft=(window.US_STATES?US_STATES.features:[]).find(f=>f.properties.n===code); if(!ft||typeof d3==='undefined')return null;
    const pr=d3.geoMercator().fitExtent(box,ft), g=el('g',{opacity:0},$('states'));
    const pa=el('path',{d:d3.geoPath(pr)(ft),fill:'none','stroke-width':2,'stroke-linejoin':'round'},g); pa.style.stroke='var(--ink)';
    const [x,y]=pr([ll[1],ll[0]]);
    el('text',{x:(box[0][0]+box[1][0])/2,y:box[1][1]+44,'text-anchor':'middle',class:'city'},g,label);
    return {g,x,y};
  }
  const SB=MOBILE?[[[150,90],[450,520]],[[590,150],[830,460]]]:[[[250,120],[450,440]],[[600,170],[740,400]]];
  const stB=drawState('CA',SB[0],[35.37,-119.02],'bakersfield, ca'), stI=drawState('IN',SB[1],[39.77,-86.16],'indianapolis, in');
  const SDOT=MOBILE?34:24;

  /* ---------- headline word splitting ---------- */
  document.querySelectorAll('.sa .hd .h').forEach(h=>{
    const walk=n=>{[...n.childNodes].forEach(c=>{if(c.nodeType===3){const f=document.createDocumentFragment();c.textContent.split(/(\s+)/).forEach(t=>{if(!t)return;if(/^\s+$/.test(t))f.appendChild(document.createTextNode(t));else{const s=document.createElement('span');s.className='w';s.textContent=t;f.appendChild(s)}});c.replaceWith(f)}else walk(c)})};walk(h)});
  const words=id=>$(id).querySelectorAll('.w'), sub=id=>$(id).querySelector('.s');

  if(typeof gsap==='undefined')return;   // library blocked: frame 1 stays readable
  gsap.registerPlugin(ScrollTrigger);

  /* ---------- on-load pop, from a visible resting state ---------- */
  if(!reduce&&first){
    gsap.from('#sa-bak',{scale:.84,transformOrigin:'50% 50%',duration:1,ease:'elastic.out(1,.5)'});
    gsap.from('#sa-cap1',{x:-16,duration:.8,ease:'power3.out'});
  }

  /* ---------- the scrubbed timeline ---------- */
  const tl=gsap.timeline({defaults:{ease:'power3.inOut',duration:1}});
  const hdIn=(id,at)=>{tl.set('#sa-'+id,{opacity:1},at);
    tl.fromTo(words(id),{opacity:0,y:24,filter:'blur(8px)'},{opacity:1,y:0,filter:'blur(0px)',stagger:.045,duration:.6,ease:'power3.out'},at);
    tl.fromTo(sub(id),{opacity:0,y:10},{opacity:1,y:0,duration:.5,ease:'power2.out'},at+.3)};
  const hdOut=(id,at)=>{tl.to(words(id),{opacity:0,y:-18,filter:'blur(6px)',stagger:.02,duration:.4,ease:'power2.in'},at);
    tl.to(sub(id),{opacity:0,duration:.3},at);tl.set('#sa-'+id,{opacity:0},at+.6)};
  const count=(node,from,to,dec,suffix,at,dur)=>{const o={v:from};tl.to(o,{v:to,duration:dur||1,ease:'power2.out',onUpdate:()=>node.textContent=o.v.toFixed(dec)+suffix},at)};

  // frame 0: "some of these cities are used to air pollution." then "some aren't." rises up with its ball to meet it
  tl.fromTo(['#sa-ind','#sa-cap2'],{y:300,opacity:0},{y:0,opacity:1,duration:1.1,ease:'power3.out',stagger:.08},.2);

  // "and because of that, they respond differently": both captions and balls step aside for the nine-city bars
  tl.to(['#sa-cap1','#sa-cap2'],{opacity:0,x:40,filter:'blur(6px)',stagger:.05,duration:.5,ease:'power2.in'},1.8);
  tl.to(['#sa-bak','#sa-ind'],{opacity:0,scale:.6,transformOrigin:'50% 50%',duration:.5,ease:'power2.in'},1.85);
  hdIn('hb',2.1);
  bars.forEach((b,i)=>{tl.set(b.g,{opacity:1},2.3);
    tl.to(b.r,{attr:{width:b.w},duration:.7,ease:'expo.out'},2.3+i*.09);
    tl.to(b.v,{opacity:1,duration:.3},2.7+i*.09)});
  tl.to({},{duration:.6},3.6);   // hold
  hdOut('hb',4.3);
  tl.to(bars.map(b=>b.g),{opacity:0,duration:.4,stagger:.02},4.3);

  // "even when the danger is the same." on its own
  hdIn('he',4.8); hdOut('he',6.0);

  // "let's take a look at two cities": state outlines; each city's ball drops in as the dot in its state
  hdIn('ht',6.4);
  [[stB,'#sa-bak'],[stI,'#sa-ind']].forEach(([st,id],i)=>{ if(!st)return;
    tl.to(st.g,{opacity:1,duration:.6},6.6+i*.15);
    tl.set(id,{scale:1,attr:{x:st.x-SDOT/2,y:st.y-SDOT/2,width:SDOT,height:SDOT,rx:SDOT/2}},6.5);
    tl.to(id,{opacity:1,duration:.4,ease:'power2.out'},6.9+i*.15)});
  if(!stB||!stI) tl.to(['#sa-bak','#sa-ind'],{opacity:1,scale:1,duration:.5},6.9);
  hdOut('ht',8.2);
  tl.to([stB&&stB.g,stI&&stI.g].filter(Boolean),{opacity:0,duration:.5},8.3);

  // "in its worst week, ... the same level of unhealthy air": the dots rise onto lollipops at equal height
  let t=9;
  tl.to(base,{strokeDashoffset:0,duration:1,ease:'expo.inOut'},t+.3);
  tl.to('#sa-bak',{attr:{x:CB-DOT/2,y:upHarm(55)-DOT/2,width:DOT,height:DOT,rx:DOT/2},duration:1.3,ease:'expo.inOut'},t+.15);
  tl.to('#sa-ind',{attr:{x:CI-DOT/2,y:upHarm(55)-DOT/2,width:DOT,height:DOT,rx:DOT/2},duration:1.3,ease:'expo.inOut'},t+.25);
  tl.to([stemTB,stemTI],{attr:{y2:upHarm(55)},duration:.8,ease:'power3.out'},t+1.1);
  tl.to([cityB,cityI],{opacity:1,duration:.4},t+1);
  tl.to([harmB.g,harmI.g],{opacity:1,duration:.4},t+1.3);
  count(harmB.n,0,55,0,'',t+1.3,.7); count(harmI.n,0,55,0,'',t+1.3,.7);
  hdIn('h2',t+.9);
  tl.to('#sa-fnote',{opacity:1,duration:.5},t+1.4);

  // "but they reacted way differently": grey dots drop below the line
  t=11.6;
  hdOut('h2',t); tl.to('#sa-fnote',{opacity:0,duration:.3},t); hdIn('h3',t+.5);
  tl.to([dB,dI],{attr:{r:DOT/2},duration:.4,ease:'back.out(2)'},t+.4);
  tl.to([dB,stemDB],{attr:{cy:down(4.8),y2:down(4.8)},duration:1,ease:'expo.out'},t+.7);
  tl.to([dI,stemDI],{attr:{cy:down(9.5),y2:down(9.5)},duration:1.4,ease:'expo.out'},t+.8);
  tl.to([talkB.g,talkI.g],{opacity:1,duration:.4},t+1.2);
  count(talkB.n,1,4.8,1,'×',t+1.2,.8); count(talkI.n,1,9.5,1,'×',t+1.2,1.1);
  // highlight the jump: a dashed guide at bakersfield's level, and the extra drop to 9.5× marked beside indianapolis's stem
  const jx=CI-DOT/2-16, jy0=down(4.8), jy1=down(9.5);
  const jump=el('g',{opacity:0},gLab);
  const guide=el('line',{x1:CB+DOT/2+6,x2:CI,y1:jy0,y2:jy0,'stroke-width':1.5,'stroke-dasharray':'5 5'},jump); guide.style.stroke='var(--ink-2)';
  const seg=el('path',{d:`M${jx-6},${jy0} H${jx} V${jy1} H${jx-6}`,fill:'none','stroke-width':3,'stroke-linecap':'round','stroke-linejoin':'round'},jump); seg.style.stroke='var(--react)';
  const jt=el('text',{x:jx-14,y:(jy0+jy1)/2+6,'text-anchor':'end',class:'unit'},jump,'about 2× more'); jt.style.fill='var(--react)';
  tl.to(jump,{opacity:1,duration:.5},t+2.1);

  // "and they talked about it differently": the chart clears, each dot flies to a disk centre and blooms into rings
  t=14;
  hdOut('h3',t); hdIn('h5',t+.6);
  tl.to([harmB.g,harmI.g,talkB.g,talkI.g,cityB,cityI,jump],{opacity:0,duration:.4},t);
  tl.to([dB,dI],{attr:{r:0},duration:.4,ease:'power2.in'},t+.1);
  tl.to([stemTB,stemTI,stemDB,stemDI],{opacity:0,duration:.4},t+.1);
  tl.to(base,{strokeDashoffset:640,duration:.7,ease:'expo.in'},t+.1);
  const seed=DR*.16*DS*2;
  tl.to('#sa-bak',{attr:{x:DPOS[0][0]-seed/2,y:DPOS[0][1]-WY-seed/2,width:seed,height:seed,rx:seed/2},duration:1,ease:'expo.inOut'},t+.4);
  tl.to('#sa-ind',{attr:{x:DPOS[1][0]-seed/2,y:DPOS[1][1]-WY-seed/2,width:seed,height:seed,rx:seed/2},duration:1,ease:'expo.inOut'},t+.45);
  [diskB,diskI].forEach((d,i)=>{
    tl.to([d.frame,d.head],{opacity:1,duration:.5},t+1.1);
    tl.to(d.layers,{opacity:(j,e)=>+e.dataset.op,duration:.25,stagger:.05,ease:'none'},t+1.3);
  });
  tl.to(['#sa-bak','#sa-ind'],{opacity:0,duration:.6},t+1.6);
  const endB=t+1.3+diskB.layers.length*.05, endI=t+1.3+diskI.layers.length*.05;
  tl.to([diskB.labs,diskB.foot],{opacity:1,duration:.4},endB);
  tl.to([diskI.labs,diskI.foot],{opacity:1,duration:.4},endI);

  // "why?" on its own while the disks clear
  t=Math.max(endB,endI)+1.4;
  hdOut('h5',t); hdIn('hw',t+.5);
  [diskB,diskI].forEach(d=>tl.to([d.frame,d.head,d.labs,d.foot,...d.layers],{opacity:0,duration:.5},t));
  hdOut('hw',t+1.9);

  // "their perception of normal is different": the chart comes back, and the top dots are re-measured against each city's own normal
  t+=2.3;
  hdIn('h4',t+.4);
  tl.to(base,{strokeDashoffset:0,duration:.8,ease:'expo.inOut'},t+.3);
  tl.to([stemTB,stemTI,stemDB,stemDI],{opacity:1,duration:.4},t+.5);
  tl.to([dB,dI],{attr:{r:DOT/2},duration:.4,ease:'back.out(2)'},t+.6);
  tl.to([cityB,cityI,talkB.g,talkI.g],{opacity:1,duration:.4},t+.7);
  tl.to('#sa-bak',{opacity:1,attr:{x:CB-DOT/2,y:upNorm(2.9)-DOT/2,width:DOT,height:DOT,rx:DOT/2},duration:1.1,ease:'expo.inOut'},t+.4);
  tl.to('#sa-ind',{opacity:1,attr:{x:CI-DOT/2,y:upNorm(4.4)-DOT/2,width:DOT,height:DOT,rx:DOT/2},duration:1.1,ease:'expo.inOut'},t+.46);
  tl.to(stemTB,{attr:{y2:upNorm(2.9)},duration:1.1,ease:'expo.inOut'},t+.4);
  tl.to(stemTI,{attr:{y2:upNorm(4.4)},duration:1.1,ease:'expo.inOut'},t+.46);
  tl.to([normB.g,normI.g],{opacity:1,duration:.4},t+1.4);
  count(normB.n,1,2.9,1,'×',t+1.4,.7); count(normI.n,1,4.4,1,'×',t+1.4,.7);

  // focus on each city in turn: grey out the other one
  const sideB=['#sa-bak',stemTB,stemDB,dB,normB.g,talkB.g,cityB], sideI=['#sa-ind',stemTI,stemDI,dI,normI.g,talkI.g,cityI];
  t+=2.8;
  hdOut('h4',t); hdIn('hf',t+.5);
  tl.to(sideI,{opacity:.16,duration:.6,ease:'power2.inOut'},t+.3);
  t+=2.4;
  hdOut('hf',t); hdIn('hi',t+.5);
  tl.to(sideI,{opacity:1,duration:.6,ease:'power2.inOut'},t+.3);
  tl.to(sideB,{opacity:.16,duration:.6,ease:'power2.inOut'},t+.3);

  // the story now ends on the Indianapolis frame; "see the numbers" follows it, then the closing line as its own section (Gina, Oct 6)
  t+=1.6;
  tl.to({},{duration:.6},t); // hold the last frame

  const st=ScrollTrigger.create({trigger:'#sa-story',start:'top top',end:'bottom bottom',scrub:reduce?true:0.8,animation:tl});
  built={st,tl}; first=false;
  }
  build();
  PHONE.addEventListener('change',()=>{build();ScrollTrigger.refresh()});
})();
