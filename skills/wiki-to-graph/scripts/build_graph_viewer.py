#!/usr/bin/env python3
"""
build_graph_viewer.py — render a graph.json (from wiki_to_graph build) into a
single self-contained, offline interactive HTML graph viewer.

Usage:
  python3 build_graph_viewer.py graph.json -o graph-viewer.html
"""
import argparse, json, os

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Knowledge Graph Viewer</title>
<style>
  :root{--bg:#12162b;--panel:#1a1f3a;--ink:#e8e8f0;--muted:#9aa0b4;--edge:#333a57;}
  *{box-sizing:border-box} html,body{margin:0;height:100%}
  body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
       background:var(--bg);color:var(--ink);overflow:hidden}
  #bar{position:fixed;top:0;left:0;right:0;height:46px;background:var(--panel);
       border-bottom:1px solid var(--edge);display:flex;align-items:center;gap:14px;
       padding:0 14px;z-index:5;flex-wrap:wrap}
  #bar h1{font-size:14px;margin:0;font-weight:600}
  #bar .count{color:var(--muted);font-size:12px}
  #bar input[type=search]{background:#0e1226;border:1px solid var(--edge);color:var(--ink);
       border-radius:6px;padding:4px 8px;font-size:12px;width:170px}
  .chip{font-size:11px;color:var(--muted);display:inline-flex;align-items:center;gap:4px;cursor:pointer;user-select:none}
  .chip input{accent-color:#4f7cff}
  #stage{position:absolute;top:46px;left:0;right:320px;bottom:0}
  svg{width:100%;height:100%;display:block;cursor:grab}
  #side{position:absolute;top:46px;right:0;bottom:0;width:320px;background:var(--panel);
        border-left:1px solid var(--edge);overflow-y:auto;padding:16px}
  #side h2{font-size:16px;margin:0 0 2px}
  #side .k{display:inline-block;font-size:10px;text-transform:uppercase;letter-spacing:.6px;
        padding:2px 7px;border-radius:10px;color:#fff;margin-bottom:10px}
  #side .deg{color:var(--muted);font-size:12px;margin:2px 0 10px;word-break:break-all}
  #side .deg code{font-size:11px;background:#0e1226;padding:1px 4px;border-radius:4px}
  #side p{font-size:13px;line-height:1.5}
  #side h3{font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:var(--muted);margin:14px 0 6px}
  #side .e{font-size:12px;padding:6px 0;border-bottom:1px solid #232842;cursor:pointer}
  #side .e:hover{background:#1e2442}
  #side .e .tgt{color:var(--ink);font-weight:500}
  #side .e .why{display:block;color:var(--muted);font-size:11px;line-height:1.45;margin-top:3px}
  #side .e .why.none{opacity:.45;font-style:italic}
  #side .et{font-size:9px;padding:1px 5px;border-radius:8px;color:#fff;margin-right:6px}
  #side .grp{display:flex;align-items:center;gap:6px;margin:16px 0 4px}
  #side .grp .nm{font-size:10px;text-transform:uppercase;letter-spacing:.7px;color:#fff;
       padding:2px 7px;border-radius:9px}
  #side .grp .ct{font-size:11px;color:var(--muted)}
  #side .body{font-size:12.5px;line-height:1.6;color:#cfd3e4}
  #side .body p{margin:0 0 9px}
  #side .body h3.mdh,#side .body h4.mdh,#side .body h5.mdh{
       font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:#aab0c6;
       margin:14px 0 5px;font-weight:600;text-transform:none;font-size:12.5px}
  #side .body ul,#side .body ol{margin:0 0 9px;padding-left:18px}
  #side .body li{margin:2px 0}
  #side .body blockquote{margin:0 0 9px;padding:2px 0 2px 10px;border-left:2px solid #3a4166;color:var(--muted)}
  #side .body pre{background:#0e1226;border:1px solid var(--edge);border-radius:6px;
       padding:8px 10px;overflow-x:auto;margin:0 0 9px}
  #side .body pre code{font-size:11px;line-height:1.45;background:none;padding:0}
  #side .body code{background:#0e1226;padding:1px 4px;border-radius:4px;font-size:11.5px}
  #side .tw{overflow-x:auto;margin:0 0 10px}
  #side .body table{border-collapse:collapse;font-size:11.5px;min-width:100%}
  #side .body th,#side .body td{border:1px solid var(--edge);padding:4px 7px;text-align:left;vertical-align:top}
  #side .body th{background:#0e1226;color:var(--ink);font-weight:600;white-space:nowrap}
  #side .why .hint{opacity:.5;font-style:italic}
  #side .why .src{color:#7f9cff;font-style:normal;opacity:.8}
  #side details.expl{margin:10px 0 4px}
  #side details.expl summary{font-size:11px;text-transform:uppercase;letter-spacing:.6px;
       color:var(--muted);cursor:pointer;user-select:none;margin-bottom:8px}
  #side .srcs{font-size:11px;color:var(--muted);line-height:1.5;margin:2px 0 0;padding-left:15px}
  #side .back{font-size:11px;color:#7f9cff;cursor:pointer;display:inline-block;margin-bottom:8px}
  #side .back:hover{text-decoration:underline}
  .legend{font-size:11px;color:var(--muted)}
  .legend b{color:var(--ink);font-weight:600}
  .legend .row{margin:3px 0;display:flex;align-items:center;gap:2px}
  .legend .swatch{display:inline-block;width:18px;border-top:2px solid;margin-right:5px;flex:none}
  details#legendwrap{border-bottom:1px solid var(--edge);padding-bottom:10px;margin-bottom:12px}
  details#legendwrap summary{font-size:11px;text-transform:uppercase;letter-spacing:.6px;
       color:var(--muted);cursor:pointer;user-select:none;margin-bottom:8px}
  svg.panning{cursor:grabbing}
  #zoomctl{position:absolute;left:12px;bottom:12px;display:flex;gap:6px;z-index:4}
  #zoomctl button{background:var(--panel);border:1px solid var(--edge);color:var(--ink);
       border-radius:6px;width:28px;height:28px;font-size:15px;cursor:pointer;line-height:1;padding:0}
  #zoomctl button:hover{border-color:#4f7cff}
  #zoomctl button.wide{width:auto;padding:0 10px;font-size:11px}
  .dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:4px;vertical-align:middle}
  text{pointer-events:none;fill:var(--muted);font-size:9px}
  .node circle{cursor:pointer;stroke:#0e1226;stroke-width:1px}
  .node.sel circle{stroke:#fff;stroke-width:2.5px}
  .node.dim{opacity:.15}
  line.dim{opacity:.04}
</style></head>
<body>
<div id="bar">
  <h1>Knowledge Graph</h1><span class="count" id="count"></span>
  <input type="search" id="search" placeholder="find a node…" autocomplete="off">
  <span id="edgeToggles"></span>
</div>
<div id="stage"><svg id="svg"></svg>
  <div id="zoomctl">
    <button id="zin" title="Zoom in">+</button>
    <button id="zout" title="Zoom out">−</button>
    <button id="zfit" class="wide" title="Fit graph to view">fit</button>
  </div>
</div>
<div id="side">
  <details id="legendwrap" open><summary>Legend</summary>
    <div class="legend" id="legend"></div>
  </details>
  <div id="detail"><p style="color:var(--muted);font-size:13px">Click a node to inspect it.</p></div>
</div>
<script id="data" type="application/json">__DATA__</script>
<script>
const G = JSON.parse(document.getElementById('data').textContent);
const KIND = Object.assign({concept:'#4f7cff',schema:'#9b5cff',procedure:'#2ec27e',fact:'#f5a623'},
  // Any kind the graph actually contains that we have no colour for gets one from the palette, so a
  // custom vocabulary is legible instead of uniformly grey.
  Object.fromEntries([...new Set(G.nodes.map(n=>n.kind).filter(k=>k &&
      !['concept','schema','procedure','fact'].includes(k)))]
    .map((k,i)=>[k, ['#00b3a4','#e5484d','#d4a72c','#7aa2ff','#b07aa1','#59a14f','#ff9da7','#9c755f'][i%8]])));
const TYPEN = {source:'#8a8f9a',index:'#d4a72c',log:'#6b7280'};
const EDGE = Object.assign({mentions:'#5b6070',related:'#4f7cff',contradicts:'#e5484d',
              cites:'#7a7f8c',indexes:'#3f466b',records:'#3f466b'},
  Object.fromEntries([...new Set(G.links.map(e=>e.type))]
    .filter(t=>!['mentions','related','contradicts','cites','indexes','records'].includes(t))
    .map((t,i)=>[t, ['#4f7cff','#e5484d','#2ec27e','#f5a623','#9b5cff','#00b3a4','#b07aa1','#d4a72c'][i%8]])));
const nodeColor = n => KIND[n.kind] || TYPEN[n.type] || '#8a8f9a';

// default-visible edge types (hub edges off to reduce clutter)
// Hub edges stay off to reduce clutter; everything else the graph contains is ON by default.
// Hardcoding this list meant a custom vocabulary rendered as unconnected dots — every edge type
// present but none of them drawable.
const enabled = Object.assign(
  Object.fromEntries([...new Set(G.links.map(e=>e.type))].map(t=>[t,true])),
  {cites:false,indexes:false,records:false});

const svg = document.getElementById('svg'), NS='http://www.w3.org/2000/svg';
const byId = Object.fromEntries(G.nodes.map(n=>[n.id,n]));
let nodes = G.nodes.map(n=>({...n,x:Math.random()*800+100,y:Math.random()*600+80,vx:0,vy:0}));
let nIdx = Object.fromEntries(nodes.map((n,i)=>[n.id,i]));
const allEdges = G.links.map(e=>({...e}));
document.getElementById('count').textContent = G.nodes.length+' nodes · '+G.links.length+' edges';
let selected=null;

function visibleEdges(){ return allEdges.filter(e=>enabled[e.type] && nIdx[e.source]!=null && nIdx[e.target]!=null); }

// ---- edge-type toggles ----
const tog=document.getElementById('edgeToggles');
Object.keys(EDGE).forEach(t=>{
  const c=allEdges.filter(e=>e.type===t).length; if(!c) return;
  const lab=document.createElement('label'); lab.className='chip';
  lab.innerHTML=`<input type="checkbox" ${enabled[t]?'checked':''}> <span class="dot" style="background:${EDGE[t]}"></span>${t} (${c})`;
  lab.querySelector('input').onchange=e=>{enabled[t]=e.target.checked; sim(); draw();
    if(selected) select(selected,true);};
  tog.appendChild(lab);
});

// ---- legend ----
const KIND_DESC = {concept:'abstract idea, property, category',schema:'concrete structure, formula, architecture',
                   procedure:'process, method, technique',fact:'empirical finding or result'};
const TYPE_DESC = {source:'an ingested artifact (paper, page, book, deck…)',
                   index:'navigational hub',log:'chronological record'};
const EDGE_DESC = {mentions:'reference in body prose',related:'explicit association',
                   contradicts:'documented disagreement',cites:'provenance \u2192 source',
                   indexes:'hub listing',records:'log entry'};
const present = t => allEdges.some(e=>e.type===t);
document.getElementById('legend').innerHTML =
  '<b>Node kind</b> <span style="opacity:.65">— what the node knows</span>'+
  Object.entries(KIND).map(([k,c])=>
    `<div class="row"><span class="dot" style="background:${c}"></span>${k}${KIND_DESC[k]?` <span style="opacity:.65">— ${KIND_DESC[k]}</span>`:''}</div>`).join('')+
  '<div style="height:8px"></div><b>Node type</b> <span style="opacity:.65">— what the node is</span>'+
  Object.entries(TYPEN).map(([k,c])=>
    `<div class="row"><span class="dot" style="background:${c}"></span>${k}${TYPE_DESC[k]?` <span style="opacity:.65">— ${TYPE_DESC[k]}</span>`:''}</div>`).join('')+
  '<div style="height:8px"></div><b>Edge type</b> <span style="opacity:.65">— toggle in top bar</span>'+
  Object.keys(EDGE).filter(present).map(t=>
    `<div class="row"><span class="swatch" style="border-top-color:${EDGE[t]}${t==='cites'?';border-top-style:dashed':''}"></span>${t}${EDGE_DESC[t]?` <span style="opacity:.65">— ${EDGE_DESC[t]}</span>`:''}</div>`).join('')+
  '<div style="height:8px"></div><div class="row">Node size = in-degree \u00b7 line width = edge weight</div>'+
  '<div class="row">Scroll to zoom \u00b7 drag background to pan \u00b7 drag a node to move it</div>';

// ---- force layout ----
function sim(){
  const W=svg.clientWidth||900,H=svg.clientHeight||650, E=visibleEdges();
  const L=E.map(e=>[nIdx[e.source],nIdx[e.target]]);
  for(let it=0;it<220;it++){
    for(let i=0;i<nodes.length;i++)for(let j=i+1;j<nodes.length;j++){
      const a=nodes[i],b=nodes[j];let dx=a.x-b.x,dy=a.y-b.y,d2=dx*dx+dy*dy+.01,d=Math.sqrt(d2);
      const f=2200/d2,fx=f*dx/d,fy=f*dy/d;a.vx+=fx;a.vy+=fy;b.vx-=fx;b.vy-=fy;}
    for(const [i,j] of L){const a=nodes[i],b=nodes[j];let dx=b.x-a.x,dy=b.y-a.y,d=Math.sqrt(dx*dx+dy*dy)+.01;
      const f=(d-90)*.02,fx=f*dx/d,fy=f*dy/d;a.vx+=fx;a.vy+=fy;b.vx-=fx;b.vy-=fy;}
    for(const n of nodes){n.x+=n.vx*.4;n.y+=n.vy*.4;n.vx*=.85;n.vy*=.85;
      n.x=Math.max(30,Math.min(W-30,n.x));n.y=Math.max(30,Math.min(H-30,n.y));}
  }
}
function neighborsOf(id){const s=new Set([id]);visibleEdges().forEach(e=>{if(e.source===id)s.add(e.target);if(e.target===id)s.add(e.source);});return s;}
// ---- viewport (pan / zoom) ----
let view={k:1,x:0,y:0}, viewG=null;
function applyView(){ if(viewG) viewG.setAttribute('transform',`translate(${view.x},${view.y}) scale(${view.k})`); }
function draw(){
  const E=visibleEdges();svg.innerHTML='';
  viewG=document.createElementNS(NS,'g');svg.appendChild(viewG);
  const near=selected?neighborsOf(selected):null;
  for(const e of E){const a=nodes[nIdx[e.source]],b=nodes[nIdx[e.target]];
    const l=document.createElementNS(NS,'line');
    l.setAttribute('x1',a.x);l.setAttribute('y1',a.y);l.setAttribute('x2',b.x);l.setAttribute('y2',b.y);
    l.setAttribute('stroke',EDGE[e.type]||'#444');
    l.setAttribute('stroke-width',Math.min(4,e.weight||1));
    if(e.type==='cites')l.setAttribute('stroke-dasharray','3,3');
    if(near&&!(near.has(e.source)&&near.has(e.target)))l.setAttribute('class','dim');
    viewG.appendChild(l);}
  for(const n of nodes){
    const g=document.createElementNS(NS,'g');g.setAttribute('class','node'+(n.id===selected?' sel':'')+((near&&!near.has(n.id))?' dim':''));
    g.setAttribute('transform',`translate(${n.x},${n.y})`);g.dataset.id=n.id;
    g.onclick=()=>{if(dragMoved){dragMoved=false;return;}select(n.id);};
    const r=4+Math.min(9,(n.in_degree||0)*0.5);
    const c=document.createElementNS(NS,'circle');c.setAttribute('r',r);c.setAttribute('fill',nodeColor(n));g.appendChild(c);
    const t=document.createElementNS(NS,'text');t.setAttribute('x',r+3);t.setAttribute('y',3);
    t.textContent=n.title.length>26?n.title.slice(0,24)+'…':n.title;g.appendChild(t);
    viewG.appendChild(g);}
  applyView();
}
function esc(t){return (t||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function inl(t){return esc(t)
  .replace(/`([^`]+)`/g,'<code>$1</code>')
  .replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>')
  .replace(/(^|[\s(])\*([^*\n]+)\*(?=[\s).,;:!?]|$)/g,'$1<em>$2</em>');}

// Page prose is markdown: ### subsections, tables, fenced code, lists, quotes.
// Rendering it as flat paragraphs leaks the markup as literal text.
const UL=/^\s*[-*+]\s+/, OL=/^\s*\d+[.)]\s+/, BLOCKSTART=/^\s*(#{1,6}\s|```|>|\|)/;
function renderMd(src){
  const L=(src||'').split('\n'); const out=[]; let i=0;
  const cells=r=>r.trim().replace(/^\||\|$/g,'').split('|').map(c=>c.trim());
  while(i<L.length){
    const l=L[i];
    if(/^\s*```/.test(l)){
      const buf=[]; i++;
      while(i<L.length && !/^\s*```/.test(L[i])) buf.push(L[i++]);
      i++; out.push('<pre><code>'+esc(buf.join('\n'))+'</code></pre>'); continue;
    }
    const h=l.match(/^\s*(#{1,6})\s+(.*)$/);
    if(h){ const lvl=Math.min(5,Math.max(3,h[1].length));
      out.push('<h'+lvl+' class="mdh">'+inl(h[2])+'</h'+lvl+'>'); i++; continue; }
    if(/^\s*\|.*\|\s*$/.test(l) && i+1<L.length && /^\s*\|[\s:|-]+\|\s*$/.test(L[i+1])){
      const head=cells(l); i+=2; const rows=[];
      while(i<L.length && /^\s*\|.*\|\s*$/.test(L[i])) rows.push(cells(L[i++]));
      out.push('<div class="tw"><table><thead><tr>'+head.map(c=>'<th>'+inl(c)+'</th>').join('')+
        '</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map(c=>'<td>'+inl(c)+'</td>').join('')+'</tr>').join('')+
        '</tbody></table></div>'); continue;
    }
    if(/^\s*>/.test(l)){ const buf=[];
      while(i<L.length && /^\s*>/.test(L[i])) buf.push(L[i++].replace(/^\s*>\s?/,''));
      out.push('<blockquote>'+inl(buf.join(' '))+'</blockquote>'); continue; }
    if(UL.test(l)||OL.test(l)){
      const ordered=OL.test(l), items=[];
      while(i<L.length && (UL.test(L[i])||OL.test(L[i]))){
        let it=L[i++].replace(UL,'').replace(OL,'');
        while(i<L.length && L[i].trim() && !UL.test(L[i]) && !OL.test(L[i]) && !BLOCKSTART.test(L[i]))
          it+=' '+L[i++].trim();
        items.push('<li>'+inl(it)+'</li>');
      }
      out.push((ordered?'<ol>':'<ul>')+items.join('')+(ordered?'</ol>':'</ul>')); continue;
    }
    if(!l.trim()){ i++; continue; }
    const buf=[];
    while(i<L.length && L[i].trim() && !BLOCKSTART.test(L[i]) && !UL.test(L[i]) && !OL.test(L[i]))
      buf.push(L[i++].trim());
    out.push('<p>'+inl(buf.join(' '))+'</p>');
  }
  return out.join('');
}

// `related` and `contradicts` are symmetric: the same pair appears once as an
// outgoing edge and once as a backlink. Listing both is the same fact twice.
const SYMM={related:1,contradicts:1};

// A link with no stated reason still often has one — written in the body of either
// page. Fall back to that, and say where it came from rather than inventing it.
function reasonFor(rel,id){
  if(rel.context) return '<span class="why">'+inl(rel.context)+'</span>';
  const m=allEdges.find(e=>e.type==='mentions'&&e.context&&
    ((e.source===id&&e.target===rel.other)||(e.source===rel.other&&e.target===id)));
  if(m){ const who=m.source===id?'this page':(byId[rel.other]||{}).title;
    return '<span class="why">'+inl(m.context)+
           '<span class="src"> — from '+esc(who)+'’s body text</span></span>'; }
  return '<span class="why"><span class="hint">no reason given — add '+
         '“— why” after the link on either page</span></span>';
}

function relRows(list,id){
  const byType={};
  list.forEach(e=>{(byType[e.type]=byType[e.type]||[]).push(e);});
  return Object.keys(EDGE).filter(t=>byType[t]&&byType[t].length).map(t=>{
    const rows=byType[t].map(e=>{
      const nd=byId[e.other];
      return '<div class="e" data-go="'+e.other+'"><span class="tgt">'+esc(nd?nd.title:e.other)+'</span>'+
             (e.weight>1?' <span style="opacity:.5">×'+e.weight+'</span>':'')+reasonFor(e,id)+'</div>';
    }).join('');
    return '<div class="grp"><span class="nm" style="background:'+EDGE[t]+'">'+t+'</span>'+
           '<span class="ct">'+byType[t].length+(EDGE_DESC[t]?' · '+EDGE_DESC[t]:'')+'</span></div>'+rows;
  }).join('');
}
const NONE='<p style="color:var(--muted);font-size:12px">none with the current edge filters</p>';

let hist=[];
function select(id, viaHistory){
  if(selected && selected!==id && !viaHistory) hist.push(selected);
  selected=id;
  const n=byId[id], s=document.getElementById('detail'), col=nodeColor(n);
  const outs=(n.edges||[]).filter(e=>enabled[e.type]);
  const backs=allEdges.filter(e=>e.target===id&&enabled[e.type]);
  const symMap={};
  outs.filter(e=>SYMM[e.type]).forEach(e=>{
    symMap[e.type+'|'+e.target]={type:e.type,other:e.target,context:e.context,weight:e.weight};});
  backs.filter(e=>SYMM[e.type]).forEach(e=>{
    const k=e.type+'|'+e.source, cur=symMap[k];
    if(!cur) symMap[k]={type:e.type,other:e.source,context:e.context,weight:e.weight};
    else if((e.context||'').length>(cur.context||'').length) cur.context=e.context;});
  const sym=Object.values(symMap);
  const mk=(list,k)=>list.filter(e=>!SYMM[e.type])
    .map(e=>({type:e.type,other:e[k],context:e.context,weight:e.weight}));
  const outD=mk(outs,'target'), backD=mk(backs,'source');
  s.innerHTML=
    (hist.length?'<span class="back" id="back">← back</span>':'')+
    '<h2>'+esc(n.title)+'</h2>'+
    '<span class="k" style="background:'+col+'">'+esc(n.kind||n.type)+'</span>'+
    '<div class="deg">in-degree '+(n.in_degree||0)+' · out-degree '+(n.out_degree||0)+
      (n.n_sources!=null?' · '+n.n_sources+' source(s)':'')+
      (n.word_count?' · '+n.word_count+' words':'')+'</div>'+
    (n.type==='source'&&(n.medium||n.locator)
      ? '<div class="deg">'+(n.medium?'<b style="color:var(--ink)">'+esc(n.medium)+'</b>':'')+
        (n.medium&&n.locator?' · ':'')+(n.locator?'<code>'+esc(n.locator)+'</code>':'')+'</div>' : '')+
    (n.summary?'<div class="body">'+renderMd(n.summary)+'</div>':'')+
    (n.explanation?'<details class="expl"><summary>Full explanation</summary>'+
        '<div class="body">'+renderMd(n.explanation)+'</div></details>':'')+
    ((n.sources&&n.sources.length)
      ? '<h3>Sources</h3><ul class="srcs">'+n.sources.map(x=>'<li>'+inl(x)+'</li>').join('')+'</ul>' : '')+
    '<h3>Mutual — holds in both directions ('+sym.length+')</h3>'+(sym.length?relRows(sym,id):NONE)+
    '<h3>This page points to ('+outD.length+')</h3>'+(outD.length?relRows(outD,id):NONE)+
    '<h3>Points at this page ('+backD.length+')</h3>'+(backD.length?relRows(backD,id):NONE);
  s.querySelectorAll('.e').forEach(el=>el.onclick=()=>select(el.dataset.go));
  const b=document.getElementById('back');
  if(b) b.onclick=()=>{const p=hist.pop(); if(p) select(p,true);};
  s.scrollTop=0;
  draw();
}
document.getElementById('search').oninput=e=>{
  const q=e.target.value.toLowerCase().trim();if(!q)return;
  const hit=nodes.find(n=>n.title.toLowerCase().includes(q));if(hit)select(hit.id);
};
function fit(){
  if(!nodes.length)return;
  const W=svg.clientWidth||900,H=svg.clientHeight||650,pad=70;
  const xs=nodes.map(n=>n.x),ys=nodes.map(n=>n.y);
  const x0=Math.min(...xs),x1=Math.max(...xs),y0=Math.min(...ys),y1=Math.max(...ys);
  const k=Math.min((W-pad*2)/Math.max(1,x1-x0),(H-pad*2)/Math.max(1,y1-y0),2.5);
  view.k=Math.max(0.15,Math.min(6,k));
  view.x=(W-(x0+x1)*view.k)/2; view.y=(H-(y0+y1)*view.k)/2;
  applyView();
}
function zoomAt(mx,my,f){
  const k=Math.max(0.15,Math.min(6,view.k*f)),f2=k/view.k;
  view.x=mx-(mx-view.x)*f2; view.y=my-(my-view.y)*f2; view.k=k; applyView();
}
svg.addEventListener('wheel',ev=>{
  ev.preventDefault();
  const r=svg.getBoundingClientRect();
  zoomAt(ev.clientX-r.left, ev.clientY-r.top, Math.exp(-ev.deltaY*0.0015));
},{passive:false});

let drag=null, dragMoved=false;
svg.addEventListener('mousedown',ev=>{
  if(ev.button!==0)return;
  dragMoved=false;
  const ng=ev.target.closest&&ev.target.closest('g.node');
  if(ng){drag={mode:'node',id:ng.dataset.id};}
  else{drag={mode:'pan',sx:ev.clientX,sy:ev.clientY,ox:view.x,oy:view.y};svg.classList.add('panning');}
});
window.addEventListener('mousemove',ev=>{
  if(!drag)return;
  if(drag.mode==='pan'){
    view.x=drag.ox+(ev.clientX-drag.sx); view.y=drag.oy+(ev.clientY-drag.sy); applyView();
  }else{
    const r=svg.getBoundingClientRect(), n=nodes[nIdx[drag.id]];
    if(!n)return;
    n.x=(ev.clientX-r.left-view.x)/view.k; n.y=(ev.clientY-r.top-view.y)/view.k;
    dragMoved=true; draw();
  }
});
window.addEventListener('mouseup',()=>{svg.classList.remove('panning');drag=null;});
document.getElementById('zin').onclick=()=>zoomAt(svg.clientWidth/2,svg.clientHeight/2,1.3);
document.getElementById('zout').onclick=()=>zoomAt(svg.clientWidth/2,svg.clientHeight/2,1/1.3);
document.getElementById('zfit').onclick=fit;

window.addEventListener('resize',()=>{sim();draw();fit();});
sim();draw();fit();
</script></body></html>"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("graph")
    ap.add_argument("-o", "--out", default="graph-viewer.html")
    a = ap.parse_args()
    data = open(a.graph, encoding="utf-8").read()
    json.loads(data)  # validate
    open(a.out, "w", encoding="utf-8").write(TEMPLATE.replace("__DATA__", data))
    print("wrote", a.out)

if __name__ == "__main__":
    main()
