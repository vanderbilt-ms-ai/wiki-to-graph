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
  #side .deg{color:var(--muted);font-size:12px;margin:2px 0 10px}
  #side p{font-size:13px;line-height:1.5}
  #side h3{font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:var(--muted);margin:14px 0 6px}
  #side .e{font-size:12px;padding:3px 0;border-bottom:1px solid #232842;cursor:pointer}
  #side .e:hover{color:#fff}
  #side .et{font-size:9px;padding:1px 5px;border-radius:8px;color:#fff;margin-right:6px}
  .legend{font-size:11px;color:var(--muted)}
  .legend b{color:var(--ink);font-weight:600}
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
<div id="stage"><svg id="svg"></svg></div>
<div id="side"><div class="legend" id="legend"></div>
  <p style="color:var(--muted);font-size:13px;margin-top:14px">Click a node to inspect it.</p>
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
  lab.querySelector('input').onchange=e=>{enabled[t]=e.target.checked; sim(); draw();};
  tog.appendChild(lab);
});

// ---- legend ----
document.getElementById('legend').innerHTML =
  '<b>Node kind</b><br>'+Object.entries(KIND).map(([k,c])=>`<span class="dot" style="background:${c}"></span>${k}`).join('&nbsp; ')+
  '<br><span class="dot" style="background:#8a8f9a"></span>source &nbsp;<span class="dot" style="background:#d4a72c"></span>index/log'+
  '<br><br><b>Edge type</b> = color; toggle in top bar. Node size = degree.';

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
function draw(){
  const E=visibleEdges();svg.innerHTML='';
  const near=selected?neighborsOf(selected):null;
  for(const e of E){const a=nodes[nIdx[e.source]],b=nodes[nIdx[e.target]];
    const l=document.createElementNS(NS,'line');
    l.setAttribute('x1',a.x);l.setAttribute('y1',a.y);l.setAttribute('x2',b.x);l.setAttribute('y2',b.y);
    l.setAttribute('stroke',EDGE[e.type]||'#444');
    l.setAttribute('stroke-width',Math.min(4,e.weight||1));
    if(e.type==='cites')l.setAttribute('stroke-dasharray','3,3');
    if(near&&!(near.has(e.source)&&near.has(e.target)))l.setAttribute('class','dim');
    svg.appendChild(l);}
  for(const n of nodes){
    const g=document.createElementNS(NS,'g');g.setAttribute('class','node'+(n.id===selected?' sel':'')+((near&&!near.has(n.id))?' dim':''));
    g.setAttribute('transform',`translate(${n.x},${n.y})`);g.onclick=()=>select(n.id);
    const r=4+Math.min(9,(n.in_degree||0)*0.5);
    const c=document.createElementNS(NS,'circle');c.setAttribute('r',r);c.setAttribute('fill',nodeColor(n));g.appendChild(c);
    const t=document.createElementNS(NS,'text');t.setAttribute('x',r+3);t.setAttribute('y',3);
    t.textContent=n.title.length>26?n.title.slice(0,24)+'…':n.title;g.appendChild(t);
    svg.appendChild(g);}
}
function select(id){
  selected=id;const n=byId[id];const s=document.getElementById('side');
  const col=nodeColor(n);
  const outs=(n.edges||[]).filter(e=>enabled[e.type]);
  s.innerHTML=`<h2>${n.title}</h2>`+
    (n.kind?`<span class="k" style="background:${col}">${n.kind}</span>`:`<span class="k" style="background:${col}">${n.type}</span>`)+
    `<div class="deg">in-degree ${n.in_degree||0} · out-degree ${n.out_degree||0}`+
      (n.n_sources!=null?` · ${n.n_sources} source(s)`:'')+`</div>`+
    (n.summary?`<p>${n.summary}</p>`:'')+
    `<h3>Outgoing edges (${outs.length})</h3>`+
    outs.map(e=>{const tg=byId[e.target];return `<div class="e" data-go="${e.target}">`+
      `<span class="et" style="background:${EDGE[e.type]||'#555'}">${e.type}</span>`+
      `${tg?tg.title:e.target}${e.weight>1?' ×'+e.weight:''}</div>`;}).join('')+
    `<h3>Backlinks</h3>`+
    (allEdges.filter(e=>e.target===id&&enabled[e.type]).map(e=>{const sr=byId[e.source];
      return `<div class="e" data-go="${e.source}"><span class="et" style="background:${EDGE[e.type]||'#555'}">${e.type}</span>${sr?sr.title:e.source}</div>`;}).join('')||'<p style="color:var(--muted);font-size:12px">none (with current filters)</p>');
  s.querySelectorAll('.e').forEach(el=>el.onclick=()=>select(el.dataset.go));
  draw();
}
document.getElementById('search').oninput=e=>{
  const q=e.target.value.toLowerCase().trim();if(!q)return;
  const hit=nodes.find(n=>n.title.toLowerCase().includes(q));if(hit)select(hit.id);
};
window.addEventListener('resize',()=>{sim();draw();});
sim();draw();
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
