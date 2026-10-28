const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'Oficina_Precisao_Universal.html'), 'utf8');
const outer = /<script>([\s\S]*?)<\/script>/i.exec(html)?.[1];
assert.ok(outer, 'outer script exists');
new vm.Script(outer, {filename:'unified.js'});
const literal = /const DOCUMENTS = (\{[\s\S]*?\});\s*const frames/.exec(outer)?.[1];
assert.ok(literal, 'embedded HTML sources are present');
const docs = vm.runInNewContext('('+literal+')');
const sourceScript = key => /<script>([\s\S]*?)<\/script>/i.exec(docs[key])?.[1];

test('offline artifact embeds all four original computation engines with parseable scripts', () => {
  assert.deepEqual(Object.keys(docs).sort(), ['saw-edge','saw-grid','square-detail','square-flex']);
  for (const [key, document] of Object.entries(docs)) {
    assert.ok(document.length > 20000, `${key} retains full functionality`);
    assert.doesNotMatch(document, /navigator\.devicePosture|viewport-segment-|device-posture\s*:/);
    new vm.Script(sourceScript(key), {filename:key+'.js'});
    assert.doesNotMatch(document, /<script\s+src=|<link\s+[^>]*href=|<img\s+[^>]*src=/i);
  }
});

const vals = {
  nInputSide:'short',nInputLen:'500',nRatio:'1.5',nWidthPct:'10',nMaterial:'7075',nRobust:'1',
  nHoleMode:'functional',nThicknessMode:'auto',nManualThk:'10',
  sSize:'250',sMaterial:'7075',sBody:'frame',sFramePct:'14',sFencePct:'9',sRobust:'1',sScribe:'5',sShowPitch:'true'
};
function squareGeometry(key) {
  let source = sourceScript(key);
  if (key === 'square-detail') source = source.slice(0, source.indexOf('/* ---------- persistence / UI ---------- */'));
  else source = source.slice(0, source.indexOf('document.querySelectorAll("[data-mode]").forEach(b=>b.onclick'));
  const context = {document:{getElementById:id=>({value:vals[id],checked:true})}};
  vm.createContext(context);
  vm.runInContext(source, context);
  return vm.runInContext('({normal:calcNormal(),speed:calcSpeed()})', context);
}

test('both squares compute the same CNC geometry for common dimensions', () => {
  const technical = squareGeometry('square-detail');
  const studio = squareGeometry('square-flex');
  assert.equal(technical.normal.short, 500);
  assert.equal(technical.normal.long, 750);
  assert.equal(technical.normal.w, 50);
  assert.equal(technical.speed.A, 250);
  assert.ok(Math.abs(technical.speed.hyp - 353.553390593) < 1e-6);
  for (const part of ['normal','speed']) {
    for (const metric of ['mass','grossMass','t']) {
      assert.ok(Math.abs(technical[part][metric] - studio[part][metric]) < 1e-9,
        `${part}.${metric} consistent across engines`);
    }
  }
});

test('square engines remain consistent under material, proportion and thickness changes', () => {
  const before={...vals};
  try {
    Object.assign(vals,{nInputSide:'long',nInputLen:'600',nRatio:'2',nWidthPct:'12',nMaterial:'304',nRobust:'1.2',nHoleMode:'relief',nThicknessMode:'manual',nManualThk:'12',sSize:'500',sMaterial:'316',sBody:'solid',sFramePct:'20'});
    const a=squareGeometry('square-detail'),b=squareGeometry('square-flex');
    assert.equal(a.normal.short,300);
    assert.equal(a.normal.long,600);
    assert.equal(a.normal.w,36);
    assert.equal(a.normal.t,12);
    assert.equal(a.speed.A,500);
    for(const part of ['normal','speed'])for(const metric of ['mass','grossMass','t'])
      assert.ok(Math.abs(a[part][metric]-b[part][metric])<1e-9,part+'.'+metric);
  } finally { Object.assign(vals,before); }
});

test('edge cutter determines 15 openings and blocks short boards', () => {
  const fields = {boardW:'1900',boardH:'130',edgeReserve:'50',percent:'70',fitRule:'equal'};
  let script = sourceScript('saw-edge');
  script = script.slice(0, script.indexOf('function svgEl('));
  script += 'globalThis.getGeometry=calc;})();';
  const context = {document:{querySelector:q=>({get value(){return fields[q.slice(1)]},set value(v){fields[q.slice(1)]=v},checked:true})}};
  vm.createContext(context);vm.runInContext(script,context);
  const result = context.getGeometry();
  assert.equal(result.fit,true);
  assert.equal(result.n,15);
  assert.equal(result.required,1200);
  assert.equal(result.gaps[0],50);
  fields.boardW='100';
  const invalid=context.getGeometry();
  assert.equal(invalid.fit,false);
  assert.equal(invalid.required,1200);
});

test('parametric board creates 6 by 3 valid holes and rejects impossible margins', () => {
  const fields={W:'600',H:'250',M:'15',G:'15',D:'75',PCT:'',PMODE:'circ',ALIGN:'center',INTDIMS:false};
  let script=sourceScript('saw-grid');
  script=script.slice(0,script.indexOf('function setStatus(')).replace('render(result);','');
  script+='globalThis.getGeometry=calculate;})();';
  const context={document:{getElementById:id=>({get value(){return fields[id]},get checked(){return fields[id]===true}})}};
  vm.createContext(context);vm.runInContext(script,context);
  const result=context.getGeometry();
  assert.equal(result.nCols,6);
  assert.equal(result.nRows,3);
  assert.equal(result.holes.length,18);
  assert.ok(result.marginL>=15 && result.marginR>=15);
  fields.M='400';
  assert.throws(()=>context.getGeometry(),/reservas laterais/);
});
