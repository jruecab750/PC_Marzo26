// Prueba una página de GALía en Chromium sin pantalla: capturas y revisión de trazos.
// Uso (desde la carpeta de la página):
//   PAGINA=galia_plano2_sites.html node probar.mjs paso3@12 paso9@40      → capturas/<id>_<t>.png
//   REVISAR=1 PAGINA=... node probar.mjs                                   → lista trazos sin robot y escenas alargadas
//   VW=390 VH=640 ...                                                      → tamaño de ventana (móvil)
// Si cdn.jsdelivr.net está bloqueado, THREE_LOCAL apunta a una copia de three@0.160.0 (npm pack three@0.160.0).
import pw from '/opt/node22/lib/node_modules/playwright/index.js'; const { chromium } = pw;
const proxy = process.env.HTTPS_PROXY || process.env.https_proxy;
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-certificate-errors'], proxy: proxy ? { server: proxy } : undefined });
const page = await browser.newPage({ viewport: { width: +(process.env.VW || 1280), height: +(process.env.VH || 720) }, ignoreHTTPSErrors: true });
const three = process.env.THREE_LOCAL;
if (three) await page.route('https://cdn.jsdelivr.net/npm/three@0.160.0/**', r => {
  const f = new URL(r.request().url()).pathname.replace('/npm/three@0.160.0/', '');
  r.fulfill({ path: three.replace(/\/$/, '') + '/' + f, contentType: 'application/javascript' });
});
await page.route('https://fonts.googleapis.com/**', r => r.fulfill({ body: '', contentType: 'text/css' }));
const logs = [];
page.on('pageerror', e => logs.push(`[pageerror] ${e.message}`));
await page.goto('file://' + process.cwd() + '/' + (process.env.PAGINA || 'pcia_replanteo_sites.html'));
await page.waitForTimeout(6000);
if (process.env.REVISAR) console.log((await page.evaluate(() => window.PCia.revisar())).join('\n'));
for (const s of process.argv.slice(2)) {
  const [id, t] = s.split('@');
  await page.evaluate(([id, t]) => window.PCia.ir(id, parseFloat(t)), [id, t]);
  await page.waitForTimeout(2500);
  await page.screenshot({ path: `capturas/${process.env.VW || ''}${id}_${t}.png` });
}
if (logs.length) console.log(logs.join('\n'));
await browser.close();
