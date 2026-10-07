// Graba escenas completas en horizontal (1920 × 1080) con subtítulos, fotograma a fotograma, y guarda
// el horario de la voz (frases desplazadas por retime) para montar el audio.
//   node grabar_video.mjs galia_metodo345_sites.html inicio,metodo345 salida_dir [fps]
import pw from '/opt/node22/lib/node_modules/playwright/index.js'; const { chromium } = pw;
import fs from 'fs';
const [pagina, ids, OUT, fpsArg] = process.argv.slice(2), FPS = +(fpsArg || 25);
const DIR = '/home/user/PC_Marzo26/video_replanteo_asfalto/escenas_pcia/';
const THREE = process.env.THREE_LOCAL || '/tmp/claude-0/-home-user-PC-Marzo26/0d1222da-c9d0-5747-83c3-3a3f32499aa1/scratchpad/three/package/';
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1.5 });
await page.route('https://cdn.jsdelivr.net/npm/three@0.160.0/**', r => r.fulfill({ path: THREE + new URL(r.request().url()).pathname.replace('/npm/three@0.160.0/', ''), contentType: 'application/javascript' }));
await page.route('https://fonts.googleapis.com/**', r => r.fulfill({ body: '', contentType: 'text/css' }));
page.on('pageerror', e => console.log('ERR', e.message));
await page.goto('file://' + DIR + pagina);
await page.waitForFunction(() => window.PCia && window.PCia.grabar, null, { timeout: 60000 });
fs.mkdirSync(OUT, { recursive: true });
const info = (await page.evaluate(() => window.PCia.grabar.escenas())).filter(s => ids.split(',').includes(s.id));
fs.writeFileSync(OUT + '/horario.json', JSON.stringify({ fps: FPS, escenas: info }, null, 1));
let f = 0;
for (const sc of info) {
  await page.evaluate(id => { window.PCia.grabar.empezar(id, 0); window.PCia.grabar.subtitulos(true); }, sc.id);
  const n = Math.round(sc.dur * FPS);
  for (let i = 0; i < n; i++, f++) {
    if (i) await page.evaluate(dt => window.PCia.grabar.paso(dt), 1 / FPS);
    await page.screenshot({ path: `${OUT}/${String(f).padStart(5, '0')}.jpg`, type: 'jpeg', quality: 92 });
  }
  console.log(sc.id, n, 'fotogramas');
}
await browser.close();
