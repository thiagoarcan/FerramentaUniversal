const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');

const appPath = path.resolve(__dirname, '..', 'Oficina_Precisao_Universal.html');
const url = 'file://' + appPath;

async function withApp(run, viewport = { width: 1300, height: 900 }) {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport, acceptDownloads: true });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(url);
    await page.locator('iframe[data-engine="square-flex"]').contentFrame().locator('#nInputLen').waitFor();
    await run(page, errors);
    assert.deepEqual(errors, [], 'no uncaught page exceptions');
  } finally { await browser.close(); }
}

test('single offline HTML navigates four tools without fold hardware', async () => {
  assert.ok(fs.existsSync(appPath), 'unified HTML must exist');
  const html = fs.readFileSync(appPath, 'utf8');
  assert.ok(!/navigator\.devicePosture|viewport-segment-|device-posture\s*:/.test(html));
  await withApp(async page => {
    assert.equal(await page.locator('iframe[data-engine]').count(), 4);
    assert.equal(await page.locator('[data-category="square"].active').count(), 1);
    await page.getByRole('button', {name:'Serra-copo', exact:true}).click();
    await page.getByRole('button', {name:'Malha paramétrica', exact:true}).click();
    const grid = page.locator('iframe[data-engine="saw-grid"]').contentFrame();
    await grid.locator('#cTotal').waitFor();
    assert.notEqual(await grid.locator('#cTotal').innerText(), '—');
  });
});

test('square dimensions propagate from compact view to detailed view', async () => {
  await withApp(async page => {
    const compact = page.locator('iframe[data-engine="square-flex"]').contentFrame();
    await compact.locator('#nInputLen').fill('640');
    await page.getByRole('button', {name:'Ficha técnica',exact:true}).click();
    const detail = page.locator('iframe[data-engine="square-detail"]').contentFrame();
    assert.equal(await detail.locator('#nInputLen').inputValue(), '640');
    assert.match(await detail.locator('#nKLong').innerText(), /960/);
  });
});

test('invalid saw edge blocks data export; saw grid exports SVG', async () => {
  await withApp(async page => {
    await page.getByRole('button', {name:'Serra-copo',exact:true}).click();
    const edge = page.locator('iframe[data-engine="saw-edge"]').contentFrame();
    await edge.locator('#boardW').fill('100');
    await page.getByRole('button', {name:'Exportar dados',exact:true}).click();
    assert.equal(await page.locator('[role="alert"]').count(), 1);
    await page.getByRole('button', {name:'Malha paramétrica',exact:true}).click();
    const grid = page.locator('iframe[data-engine="saw-grid"]').contentFrame();
    await grid.locator('#D').fill('85');
    assert.ok(Number((await grid.locator('#cTotal').innerText()).replace(/\D/g,'')) > 0);
    const pending = page.waitForEvent('download');
    await page.getByRole('button', {name:'Exportar SVG',exact:true}).click();
    const download = await pending;
    assert.match(download.suggestedFilename(),/\.svg$/);
  });
});

test('offline project JSON saves and restores parameters', async () => {
  await withApp(async page => {
    const compact = page.locator('iframe[data-engine="square-flex"]').contentFrame();
    await compact.locator('#nInputLen').fill('735');
    await page.getByRole('button', {name:'Serra-copo',exact:true}).click();
    const edge = page.locator('iframe[data-engine="saw-edge"]').contentFrame();
    await edge.locator('#boardW').fill('2050');
    const pending = page.waitForEvent('download');
    await page.getByRole('button', {name:'Salvar projeto',exact:true}).click();
    const download = await pending;
    const stream = fs.readFileSync(await download.path(), 'utf8');
    const project = JSON.parse(stream);
    assert.equal(project.format, 'oficina-precisao-1');
    assert.equal(project.engines['saw-edge'].fields.boardW, '2050');
    assert.equal(project.engines['square-flex'].fields.nInputLen, '735');
    await edge.locator('#boardW').fill('1550');
    await page.locator('#projectFile').setInputFiles({name:'projeto.json',mimeType:'application/json',buffer:Buffer.from(stream)});
    assert.equal(await edge.locator('#boardW').inputValue(), '2050');
  });
});

test('mobile navigation has no horizontal page overflow', async () => {
  await withApp(async page => {
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 2), true);
    await page.getByRole('button', {name:'Serra-copo',exact:true}).click();
    await page.getByRole('button', {name:'Malha paramétrica',exact:true}).click();
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 2), true);
    const grid = page.locator('iframe[data-engine="saw-grid"]').contentFrame();
    assert.ok(await grid.locator('#svgHost svg').count() > 0);
  }, {width:375,height:812});
});
