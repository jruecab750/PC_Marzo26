// Graba clips verticales de GALía fotograma a fotograma: node grabar.mjs clips.json [solo-primer-fotograma]
import pw from '/opt/node22/lib/node_modules/playwright/index.js'; const { chromium } = pw;
import fs from 'fs';
const clips = JSON.parse(fs.readFileSync(process.argv[2], 'utf8')), probe = process.argv[3] === '1';
const DIR = '/home/user/PC_Marzo26/video_replanteo_asfalto/escenas_pcia/', OUT = '/tmp/claude-0/-home-user-PC-Marzo26/0d1222da-c9d0-5747-83c3-3a3f32499aa1/scratchpad/reel/';
const THREE = '/tmp/claude-0/-home-user-PC-Marzo26/0d1222da-c9d0-5747-83c3-3a3f32499aa1/scratchpad/three/package/';
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const FPS = 30;
for (const c of clips) {
  const page = await browser.newPage({ viewport: { width: 720, height: 1280 }, deviceScaleFactor: 1.5 });
  await page.route('https://cdn.jsdelivr.net/npm/three@0.160.0/**', r => r.fulfill({ path: THREE + new URL(r.request().url()).pathname.replace('/npm/three@0.160.0/', ''), contentType: 'application/javascript' }));
  await page.route('https://fonts.googleapis.com/**', r => r.fulfill({ body: '', contentType: 'text/css' }));
  page.on('pageerror', e => console.log('ERR', e.message));
  await page.goto('file://' + DIR + c.pagina);
  await page.waitForFunction(() => window.PCia && window.PCia.grabar, null, { timeout: 60000 });
  await page.evaluate(c => window.PCia.grabar.empezar(c.id, c.t, c.cam), c);
  const n = probe ? 1 : Math.round(c.dur * FPS);
  fs.mkdirSync(OUT + c.nombre, { recursive: true });
  for (let i = 0; i < n; i++) {
    if (i) await page.evaluate(dt => window.PCia.grabar.paso(dt), 1 / FPS);
    if (c.cam && c.cam2) { const k = n > 1 ? i / (n - 1) : 0, e = k * k * (3 - 2 * k); await page.evaluate(cm => window.PCia.grabar.camara(cm), c.cam.map((v, j) => v + (c.cam2[j] - v) * e)); }
    await page.screenshot({ path: `${OUT}${c.nombre}/${String(i).padStart(4, '0')}.png` });
  }
  console.log(c.nombre, n, 'fotogramas');
  await page.close();
}
await browser.close();
