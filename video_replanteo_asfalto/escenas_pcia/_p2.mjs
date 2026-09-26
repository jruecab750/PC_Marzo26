import pw from '/opt/node22/lib/node_modules/playwright/index.js'; const { chromium } = pw;
const proxy = process.env.HTTPS_PROXY || process.env.https_proxy;
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-certificate-errors'], proxy: proxy ? { server: proxy } : undefined });
const page = await browser.newPage({ viewport: { width: +(process.env.VW || 1280), height: +(process.env.VH || 720) }, ignoreHTTPSErrors: true });
const logs = [];
await page.route('https://cdn.jsdelivr.net/npm/three@0.160.0/**', r => {
  const u = new URL(r.request().url()); const f = u.pathname.replace('/npm/three@0.160.0/', '');
  r.fulfill({ path: '/tmp/claude-0/-home-user-PC-Marzo26/0d1222da-c9d0-5747-83c3-3a3f32499aa1/scratchpad/three/package/' + f, contentType: 'application/javascript' });
});
await page.route('https://fonts.googleapis.com/**', r => r.fulfill({ body: '', contentType: 'text/css' }));
page.on('console', m => logs.push(`[${m.type()}] ${m.text()}`));
page.on('pageerror', e => logs.push(`[pageerror] ${e.message}`));
await page.goto('file://' + process.cwd() + '/galia_plano2_sites.html');
await page.waitForTimeout(6000);
await page.screenshot({ path: `capturas/${process.env.VW || ''}00_portada.png` });
console.log(logs.join("\n"));
console.log((await page.evaluate(() => window.PCia.revisar())).join('\n')); const shots = process.argv.slice(2);
for (const s of shots) {
  const [id, t] = s.split('@');
  await page.evaluate(([id, t]) => window.PCia.ir(id, parseFloat(t)), [id, t]);
  await page.waitForTimeout(2500);
  await page.screenshot({ path: `capturas/p2_${id}_${t}.png` });
}

console.log(logs.slice(0, 30).join('\n'));
await browser.close();
