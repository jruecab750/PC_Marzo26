// Imprime los HTML de esta carpeta a PDF A4 (escala exacta): node pdf.mjs a.html b.html ...
import pw from '/opt/node22/lib/node_modules/playwright/index.js'; const { chromium } = pw;
const proxy = process.env.HTTPS_PROXY || process.env.https_proxy;
const browser = await chromium.launch({ args: ['--ignore-certificate-errors'], proxy: proxy ? { server: proxy } : undefined });
for (const f of process.argv.slice(2)) {
  const page = await browser.newPage({ ignoreHTTPSErrors: true });
  await page.goto('file://' + process.cwd() + '/' + f, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.pdf({ path: f.replace(/\.html$/, '.pdf'), preferCSSPageSize: true, printBackground: true });
  console.log(f.replace(/\.html$/, '.pdf'), await page.evaluate(() => [...document.fonts].filter(x => x.status === 'loaded').map(x => x.family).join(',')));
}
await browser.close();
