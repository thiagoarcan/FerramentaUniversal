"""Build a single offline application from the four original HTML engines."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source_html"
TARGET = ROOT / "Oficina_Precisao_Universal.html"

ENGINES = {
    "square-flex": "projetista_esquadros_galaxy_flip_flex_v4.html",
    "square-detail": "projetista_esquadros_cnc_mobile_v3.html",
    "saw-edge": "croqui_serra_copo_interativo_mobile_v3.html",
    "saw-grid": "croqui_serra_copo_parametrico_v3.html",
}

V4_STYLE = """
<style>
/* Standard responsive monitor/tablet/phone behavior, without hinge adaptation. */
html,body{touch-action:pan-x pan-y}
#app{grid-template-columns:1fr;grid-template-rows:minmax(220px,45%) minmax(0,55%);}
#controlPane .controlPanel{overflow:auto}
#controlPane .formGrid{grid-auto-rows:minmax(60px,auto)}
@media(min-width:900px){
  #app{grid-template-columns:minmax(0,56%) minmax(360px,44%);grid-template-rows:1fr}
  #previewPane{border-bottom:0;border-right:1px solid #7a969f}
  #controlPane{grid-template-rows:36px 34px 1fr 30px}
}
@media(max-width:599px){
  #app{grid-template-rows:minmax(185px,39%) minmax(0,61%)}
  .previewStats{grid-template-columns:repeat(4,minmax(0,1fr))}
  .stat b{font-size:11px}
  #controlPane{grid-template-rows:34px 31px 1fr 27px;gap:4px}
}
</style>
"""

BRIDGE_EDGE = """
window.__precisionEdge={
  snapshot:()=>({tools:[...tools],seq:[...seq]}),
  restore:s=>{
    if(!Array.isArray(s.tools)||!Array.isArray(s.seq))return;
    const t=s.tools.map(Number), q=s.seq.map(Number);
    if(t.length<1||t.length>10||q.length>100||t.some(x=>!Number.isFinite(x)||x<=0||x>1000)||q.some(x=>!t.includes(x)))return;
    tools=t;seq=q;renderTools();renderSequence();update();
  },
  valid:()=>calc().fit
};
"""

BRIDGE_GRID = """
window.__precisionGrid={valid:()=>!!current, refresh:()=>safeCalc()};
"""

HTML = r"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="theme-color" content="#101a22">
  <title>Oficina de Precisão — Projetista Universal</title>
  <style>
    :root{color-scheme:dark;--bg:#0d171f;--panel:#162630;--panel2:#1e3440;--stroke:#35515f;--text:#e8f3f4;--muted:#a4bac1;--accent:#50d1c2;--gold:#f5b862;--danger:#ff978e}
    *{box-sizing:border-box}
    html,body{margin:0;min-height:100%;height:100%;width:100%;overflow:hidden;font:14px system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--bg);color:var(--text)}
    button,input{font:inherit}
    button{cursor:pointer;touch-action:manipulation}
    button:focus-visible{outline:2px solid #fff;outline-offset:2px}
    .shell{height:100%;height:100dvh;display:grid;grid-template-rows:auto auto minmax(0,1fr) auto;min-width:0;overflow:hidden}
    .header{background:#111e27;border-bottom:1px solid var(--stroke);display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 18px;min-width:0}
    .brand{display:flex;align-items:center;gap:12px;min-width:0}
    .mark{width:42px;height:42px;display:grid;place-items:center;background:linear-gradient(140deg,#2c827d,#2a4254);border:1px solid #5cb7aa;border-radius:12px;color:#f4fbf6;font-size:22px;font-weight:900;flex:none}
    .brand h1{margin:0;font-size:18px;letter-spacing:.015em;font-weight:790;line-height:1.2}
    .brand p{margin:2px 0 0;font-size:11px;color:var(--muted)}
    .righthead{display:flex;align-items:center;gap:7px;flex-wrap:wrap;justify-content:flex-end}
    .offline{font-weight:750;font-size:11px;color:#9df0bf;background:#194536;border:1px solid #367456;border-radius:100px;padding:6px 9px;white-space:nowrap}
    .headbtn,.action,.subtab,.category{background:var(--panel);border:1px solid var(--stroke);color:var(--text);border-radius:9px;min-height:38px;padding:7px 12px;font-weight:650}
    .headbtn:hover,.action:hover,.subtab:hover{background:#254350}
    .headbtn.important,.action.primary{background:#266b66;border-color:#4db5a8;color:white}
    .nav{display:flex;align-items:center;gap:14px;padding:9px 18px 10px;background:var(--panel);border-bottom:1px solid var(--stroke);min-width:0}
    .categories,.subtabs,.actions{display:flex;gap:7px;align-items:center;min-width:0}
    .category{min-height:43px;padding:9px 18px;font-size:14px;white-space:nowrap}
    .category.active{background:#285a59;border-color:#56baad;color:white}
    .subtabs{flex:1;overflow-x:auto;scrollbar-width:thin}
    .subtab{min-height:37px;font-size:12px;color:#b9d0d6;white-space:nowrap}
    .subtab.active{background:#324c58;border-color:#7ca9b0;color:white}
    .actions{margin-left:auto;flex-wrap:wrap;justify-content:flex-end}
    .action{min-height:36px;font-size:12px;white-space:nowrap}
    .workspace{min-width:0;min-height:0;position:relative;background:#0f1a22}
    .engine-frame{position:absolute;inset:0;width:100%;height:100%;border:0;background:#102029;display:none}
    .engine-frame.active{display:block}
    .footer{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:6px 18px;min-height:29px;background:#101e27;color:#a5bec6;border-top:1px solid var(--stroke);font-size:11px}
    .footer strong{color:var(--accent)}
    .toast{position:absolute;z-index:90;left:50%;bottom:22px;transform:translateX(-50%);max-width:min(650px,94%);color:#f8fcfd;background:#174e49;border:1px solid #4bb9a9;border-radius:10px;padding:10px 16px;box-shadow:0 12px 35px #0008;font-size:13px;display:none}
    .toast.error{background:#5c2829;border-color:#df6b6b}
    .toast.visible{display:block}
    [hidden]{display:none!important}
    @media(max-width:1180px){
      .nav{flex-wrap:wrap;gap:8px}
      .categories{flex:1}
      .subtabs{flex:2}
      .actions{width:100%;margin-left:0;justify-content:flex-end}
    }
    @media(max-width:700px){
      .header{padding:8px 10px;gap:8px}
      .mark{width:35px;height:35px;font-size:20px;border-radius:9px}
      .brand{gap:7px}
      .brand h1{font-size:14px}
      .brand p{font-size:10px}
      .offline{display:none}
      .headbtn{padding:7px 9px;min-height:33px;font-size:11px}
      .nav{padding:7px 8px;gap:7px}
      .categories,.subtabs{width:100%;flex:auto}
      .category{flex:1;min-height:39px;text-align:center}
      .subtab{flex:1;font-size:11px;padding:5px 8px}
      .actions{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));width:100%;gap:5px}
      .action{padding:6px 3px;font-size:10px;min-height:34px}
      .footer{padding:5px 9px;font-size:10px}
    }
    @media(max-width:380px){
      .brand p{display:none}
      .headbtn{padding:6px}
      .action{font-size:9px}
    }
    @media print{
      .header,.nav,.footer,.toast{display:none!important}
      html,body,.shell,.workspace{height:100%!important;overflow:visible!important;display:block!important}
      .engine-frame:not(.active){display:none!important}
      .engine-frame.active{display:block;position:static;width:100%;height:100vh}
    }
  </style>
</head>
<body>
  <div class="shell" id="shell">
    <header class="header">
      <div class="brand">
        <div class="mark" aria-hidden="true">∟</div>
        <div><h1>OFICINA <span style="color:var(--accent)">DE PRECISÃO</span></h1><p>Projetista universal · Esquadros & serras-copo</p></div>
      </div>
      <div class="righthead">
        <span class="offline">● 100% offline</span>
        <button class="headbtn" id="openProject" title="Importar projeto JSON">Abrir projeto</button>
        <button class="headbtn important" id="saveProject">Salvar projeto</button>
        <input type="file" id="projectFile" accept=".json,application/json" hidden>
      </div>
    </header>
    <nav class="nav" aria-label="Ferramentas">
      <div class="categories">
        <button class="category active" data-category="square" aria-label="Esquadros" aria-pressed="true">▱ Esquadros</button>
        <button class="category" data-category="saw" aria-label="Serra-copo" aria-pressed="false">◎ Serra-copo</button>
      </div>
      <div class="subtabs" id="subtabs" aria-label="Modo de trabalho">
        <button class="subtab active" data-view="square-flex" aria-pressed="true">Estúdio visual</button>
        <button class="subtab" data-view="square-detail" aria-pressed="false">Ficha técnica</button>
      </div>
      <div class="actions">
        <button class="action primary" id="exportSvg">Exportar SVG</button>
        <button class="action" id="exportData">Exportar dados</button>
        <button class="action" id="printView">Imprimir / PDF</button>
      </div>
    </nav>
    <main class="workspace" id="workspace">
      <iframe class="engine-frame active" data-engine="square-flex" title="Esquadros: estúdio visual" loading="eager"></iframe>
      <iframe class="engine-frame" data-engine="square-detail" title="Esquadros: ficha técnica" loading="eager"></iframe>
      <iframe class="engine-frame" data-engine="saw-edge" title="Serra-copo: recortes ao longo da borda" loading="eager"></iframe>
      <iframe class="engine-frame" data-engine="saw-grid" title="Serra-copo: malha paramétrica" loading="eager"></iframe>
      <div class="toast" id="toast" role="alert" aria-live="assertive"></div>
    </main>
    <footer class="footer"><span id="viewHint">Esquadro em L ou rápido · parâmetros editáveis e desenho CNC</span><strong>mm · projeto local</strong></footer>
  </div>
  <script>
    const DOCUMENTS = __DOCUMENTS__;
    const frames = Object.fromEntries([...document.querySelectorAll('iframe[data-engine]')].map(f=>[f.dataset.engine,f]));
    const subtabs = document.getElementById('subtabs');
    const toast = document.getElementById('toast');
    const categoryViews = {
      square:[['square-flex','Estúdio visual'],['square-detail','Ficha técnica']],
      saw:[['saw-edge','Recortes na borda'],['saw-grid','Malha paramétrica']]
    };
    const hints = {
      'square-flex':'Esquadro em L e rápido · projeto compacto com desenho SVG',
      'square-detail':'Dimensionamento, materiais, massa, alertas e critérios técnicos',
      'saw-edge':'Sequência de diâmetros diferentes · aberturas de borda e cotas acumuladas',
      'saw-grid':'Malha de furos · reservas, alinhamento, cotas e posição dos centros'
    };
    let category='square', activeView='square-flex', syncing=false, ready=new Set();
    function notice(message,error=false){
      toast.textContent=message;toast.className='toast visible'+(error?' error':'');
      clearTimeout(notice.timer);notice.timer=setTimeout(()=>toast.className='toast',4800);
    }
    function current(){return frames[activeView].contentDocument}
    function clickChild(selector){
      const btn=current()?.querySelector(selector);
      if(!btn){notice('Esta ação ainda não está disponível.',true);return false}
      btn.click();return true
    }
    function selectView(key){
      if(!frames[key])return;
      activeView=key;
      for(const [id,frame] of Object.entries(frames)){
        const chosen=id===key;frame.classList.toggle('active',chosen);frame.setAttribute('aria-hidden',String(!chosen))
      }
      document.querySelectorAll('.subtab').forEach(b=>{const yes=b.dataset.view===key;b.classList.toggle('active',yes);b.setAttribute('aria-pressed',String(yes))});
      document.getElementById('viewHint').textContent=hints[key];
    }
    function selectCategory(cat){
      category=cat;
      document.querySelectorAll('.category').forEach(b=>{const yes=b.dataset.category===cat;b.classList.toggle('active',yes);b.setAttribute('aria-pressed',String(yes))});
      subtabs.replaceChildren();
      for(const [id,label] of categoryViews[cat]){
        const button=document.createElement('button');button.type='button';button.className='subtab';button.textContent=label;button.dataset.view=id;
        button.onclick=()=>selectView(id);subtabs.appendChild(button);
      }
      selectView(categoryViews[cat][0][0]);
    }
    document.querySelectorAll('.category').forEach(b=>b.onclick=()=>selectCategory(b.dataset.category));
    document.querySelectorAll('.subtab').forEach(b=>b.onclick=()=>selectView(b.dataset.view));
    function fields(doc){
      const result={};
      for(const e of doc.querySelectorAll('input[id],select[id],textarea[id]')){
        if(['file','button','submit'].includes(e.type))continue;
        result[e.id]=e.type==='checkbox'?e.checked:e.value;
      }
      return result;
    }
    function applyFields(doc,saved){
      if(!saved||typeof saved!=='object')return;
      for(const [id,value] of Object.entries(saved)){
        const e=doc.getElementById(id);
        if(!e||!['INPUT','SELECT','TEXTAREA'].includes(e.tagName)||e.type==='file')continue;
        if(e.type==='checkbox')e.checked=!!value;
        else e.value=String(value);
      }
      for(const prefix of ['nInputLen','sSize','boardW','W']){
        const e=doc.getElementById(prefix);if(e)e.dispatchEvent(new Event('input',{bubbles:true}))
      }
      const recalc=doc.getElementById('recalc');if(recalc)recalc.click();
    }
    function syncSquares(from){
      if(syncing||!ready.has('square-flex')||!ready.has('square-detail'))return;
      syncing=true;
      try{
        const dest=from==='square-flex'?'square-detail':'square-flex';
        const source=frames[from].contentDocument, target=frames[dest].contentDocument;
        const s=fields(source);
        for(const [id,val] of Object.entries(s)){
          if(!/^[ns][A-Z]/.test(id))continue;
          const e=target.getElementById(id);if(!e)continue;
          if(e.type==='checkbox')e.checked=!!val;else e.value=String(val);
        }
        ['nInputLen','sSize'].forEach(id=>target.getElementById(id)?.dispatchEvent(new Event('input',{bubbles:true})));
      }finally{syncing=false}
    }
    for(const [id,iframe] of Object.entries(frames)){
      iframe.addEventListener('load',()=>{
        ready.add(id);
        if(id.startsWith('square')){
          ['input','change'].forEach(type=>iframe.contentDocument.addEventListener(type,()=>syncSquares(id),true));
          if(ready.has('square-flex')&&ready.has('square-detail'))syncSquares('square-flex');
        }
      });
      iframe.srcdoc=DOCUMENTS[id];
    }
    function childSquareMode(doc){
      if(activeView==='square-flex')return doc.querySelector('[data-mode].active')?.dataset.mode||'normal';
      return doc.querySelector('.tab.active[data-page]')?.dataset.page||'normal';
    }
    function saveBlob(name,mime,body){
      const url=URL.createObjectURL(new Blob([body],{type:mime}));
      const a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();
      setTimeout(()=>{URL.revokeObjectURL(url);a.remove()},1500);
    }
    document.getElementById('exportSvg').onclick=()=>{
      const d=current();if(!d)return;
      if(activeView==='saw-edge'){
        if(!frames[activeView].contentWindow.__precisionEdge?.valid()){notice('A sequência não cabe na chapa. Ajuste as medidas antes de exportar.',true);return}
        const svg=d.getElementById('drawing');if(!svg||!svg.children.length){notice('Desenho indisponível.',true);return}
        const clone=svg.cloneNode(true);clone.setAttribute('xmlns','http://www.w3.org/2000/svg');
        saveBlob('croqui_recortes_borda.svg','image/svg+xml;charset=utf-8',new XMLSerializer().serializeToString(clone));
      }else if(activeView==='saw-grid'){clickChild('#saveSvg')}
      else{clickChild(childSquareMode(d)==='speed'?'#sSaveSvg':'#nSaveSvg')}
    };
    document.getElementById('exportData').onclick=()=>{
      const d=current();if(!d)return;
      if(activeView==='saw-edge'){
        if(!frames[activeView].contentWindow.__precisionEdge?.valid()){notice('Exportação bloqueada: os furos e reservas não cabem na chapa.',true);return}
        clickChild('#csvBtn');
      }else if(activeView==='saw-grid')clickChild('#saveCsv');
      else clickChild(childSquareMode(d)==='speed'?'#sSaveJson':'#nSaveJson');
    };
    document.getElementById('printView').onclick=()=>{
      if(activeView==='saw-edge'&&!frames[activeView].contentWindow.__precisionEdge?.valid()){notice('Corrija as dimensões para imprimir as cotas de fabricação.',true);return}
      frames[activeView].contentWindow?.focus();frames[activeView].contentWindow?.print();
    };
    function snapshot(){
      const engines={};
      for(const [id,frame] of Object.entries(frames)){
        const doc=frame.contentDocument;if(!doc)continue;
        const entry={fields:fields(doc)};
        if(id==='saw-edge')Object.assign(entry,frame.contentWindow.__precisionEdge?.snapshot()||{});
        engines[id]=entry;
      }
      return {format:'oficina-precisao-1',date:new Date().toISOString(),activeView,engines};
    }
    document.getElementById('saveProject').onclick=()=>saveBlob('oficina_precisao_projeto.json','application/json;charset=utf-8',JSON.stringify(snapshot(),null,2));
    const fileInput=document.getElementById('projectFile');
    document.getElementById('openProject').onclick=()=>fileInput.click();
    fileInput.onchange=async()=>{
      const file=fileInput.files?.[0];if(!file)return;
      try{
        const data=JSON.parse(await file.text());
        if(data?.format!=='oficina-precisao-1'||!data.engines||typeof data.engines!=='object'||!Object.keys(frames).every(id=>data.engines[id]?.fields&&typeof data.engines[id].fields==='object'))throw new Error('O arquivo não é um projeto compatível.');
        syncing=true;
        try{
          for(const [id,frame] of Object.entries(frames)){
            applyFields(frame.contentDocument,data.engines[id].fields);
            if(id==='saw-edge')frame.contentWindow.__precisionEdge?.restore(data.engines[id]);
            if(id==='saw-grid')frame.contentWindow.__precisionGrid?.refresh();
          }
        }finally{syncing=false}
        syncSquares('square-flex');
        const target=frames[data.activeView]?data.activeView:'square-flex';
        selectCategory(target.startsWith('square')?'square':'saw');selectView(target);
        notice('Projeto recuperado com sucesso.');
      }catch(err){notice('Não foi possível abrir: '+err.message,true)}
      fileInput.value='';
    };
    window.addEventListener('keydown',event=>{
      if((event.ctrlKey||event.metaKey)&&event.key==='s'){event.preventDefault();document.getElementById('saveProject').click()}
    });
  </script>
</body>
</html>
"""


def drop_media_block(source: str, marker: str) -> str:
    match = re.search(r"@media\s*\(" + re.escape(marker) + r"[^\{]*\{", source)
    if not match:
        raise RuntimeError(f"CSS conditional rule not found: {marker}")
    start = match.start()
    depth = 1
    i = match.end()
    while depth and i < len(source):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
        i += 1
    return source[:start] + source[i:]


def load_engine(key: str, filename: str) -> str:
    s = (SOURCE / filename).read_text(encoding="utf-8")
    if key == "square-flex":
        s = drop_media_block(s, "vertical-viewport-segments:")
        s = drop_media_block(s, "device-posture:")
        s = re.sub(r"html\.flex-posture\s+#app\s*\{[^}]*\}", "", s)
        a = s.index("/* Fold posture and viewport-segment awareness */")
        b = s.index("/* Criteria pagination */", a)
        s = s[:a] + """function applyPosture(){
  $("statusDot").style.background="#3fb9a7";
  $("postureText").textContent="Layout responsivo";
  $("foldState").textContent="Oficina universal";
}
window.addEventListener("resize",()=>setTimeout(updateAll,60));

""" + s[b:]
        s = s.replace("Galaxy Flip Flex v4", "Oficina Universal · Estúdio visual")
        s = s.replace("Flex Mode", "Modo responsivo")
        s = s.replace("maximum-scale=1,user-scalable=no", "maximum-scale=5")
        s = s.replace("</head>", V4_STYLE + "</head>")
        s = s.replace('localStorage.setItem("esquadroFlipV4",JSON.stringify(s))',
                      'try{localStorage.setItem("esquadroFlipV4",JSON.stringify(s))}catch(e){}')
        s = s.replace('localStorage.removeItem("esquadroFlipV4");location.reload()',
                      'try{localStorage.removeItem("esquadroFlipV4")}catch(e){};location.reload()')
    elif key == "square-detail":
        s = s.replace('localStorage.setItem("esquadroCNC_v2",JSON.stringify(s))',
                      'try{localStorage.setItem("esquadroCNC_v2",JSON.stringify(s))}catch(e){}')
    elif key in ("saw-edge", "saw-grid"):
        inject = BRIDGE_EDGE if key == "saw-edge" else BRIDGE_GRID
        last = s.rfind("})();")
        if last < 0:
            raise RuntimeError(f"Expected private computation closure in {filename}")
        s = s[:last] + inject + s[last:]
    return s


def main() -> None:
    docs = {key: load_engine(key, filename) for key, filename in ENGINES.items()}
    # A raw </script> in a JS literal would close the outer script prematurely.
    serialized = json.dumps(docs, ensure_ascii=False).replace("</", "<\\/")
    built = HTML.replace("__DOCUMENTS__", serialized)
    TARGET.write_text(built, encoding="utf-8")
    print(f"Gerado: {TARGET} ({TARGET.stat().st_size:,} bytes; {len(docs)} motores embutidos)")


if __name__ == "__main__":
    main()
