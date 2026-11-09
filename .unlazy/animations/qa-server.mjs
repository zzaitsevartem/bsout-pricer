// Disposable browser QA proxy. Usage: node qa-server.mjs NEXT_PORT MODE_FILE
// MODE_FILE: {"mode":"down"|"delayed-success"|"delayed-error"}
import http from 'node:http';
import { readFile } from 'node:fs/promises';

const nextPort = Number(process.argv[2]);
const modeFile = process.argv[3];
if (!nextPort || !modeFile) throw new Error('Expected NEXT_PORT and MODE_FILE');
const downProbe = http.createServer();
await new Promise((resolve) => downProbe.listen(0, '127.0.0.1', resolve));
const downPort = downProbe.address().port;
await new Promise((resolve) => downProbe.close(resolve));
const item = { id: 7, canonical_key: 'fixture', canonical_name: 'Дисплей Galaxy S20', cluster_id: null, key_attrs: null, brand: { id: 1, name: 'Samsung', slug: 'samsung' }, device: { id: 7, name: 'Galaxy S20', model_key: 'samsung-s20', brand_id: 1 }, part_type: null, quality_tier: null, min_price_retail: '1000', min_price_opt: null, offers_count: 0, stores_count: 0, store_slugs: [] };
const device = { id: 7, model_key: 'samsung-s20', name: 'Galaxy S20', brand: item.brand, aliases: [], model_codes: ['SM-G980F'], release_year: 2020, images: [], metadata_source_url: null };
const plan = { plan: 'basic', name_ru: 'Базовый', price: 490, first_payment_price: 490, currency: 'RUB', duration_days: 30, tracked_products: 10, stores: 5, fuzzy_search: false, price_alerts: true, export_reports: false, support_ru: 'email', featured: false, sort_order: 1 };
function fixture(path) {
  if (path === '/api/payment/plans') return [plan];
  if (path.startsWith('/api/devices/')) return device;
  if (path === '/api/products/catalog/facets') return { total: 1, devices: [], part_types: [], quality_tiers: [] };
  if (path === '/api/products/catalog/devices' || path === '/api/products/catalog/suggestions') return [];
  if (path === '/api/products/catalog') return { results: [item], total: 1, page: 1, per_page: 20 };
  if (/^\/api\/products\/catalog\/\d+\/price-history$/.test(path)) return { product_id: 7, days: 30, points: [] };
  if (/^\/api\/products\/catalog\/\d+$/.test(path)) return { product: item, cluster: null, offers: [], stats: { offers_count: 0, stores_count: 0, min_price_retail: null, max_price_retail: null, avg_price_retail: null, min_price_opt: null, spread_abs: null, spread_pct: null }, alternatives: [] };
  return null;
}
const server = http.createServer(async (req, res) => {
  const path = new URL(req.url, 'http://localhost').pathname;
  if (path.startsWith('/api/')) {
    try {
      const { mode, delayMs = 5000 } = JSON.parse(await readFile(modeFile, 'utf8'));
      const started = Date.now();
      console.log(`${new Date().toISOString()} START ${mode} ${req.method} ${req.url}`);
      res.on('finish', () => console.log(`${new Date().toISOString()} END ${res.statusCode} ${Date.now() - started}ms ${req.url}`));
      if (mode === 'down') {
        try { await fetch(`http://127.0.0.1:${downPort}${req.url}`); } catch { res.writeHead(502).end('Fixture backend unavailable'); return; }
        res.writeHead(502).end('Fixture down port unexpectedly available'); return;
      }
      if (!['delayed-success', 'delayed-error'].includes(mode)) throw new Error(`Unknown mode: ${mode}`);
      await new Promise((resolve) => setTimeout(resolve, Math.max(0, Number(delayMs) || 0)));
      const body = fixture(path);
      res.writeHead(mode === 'delayed-error' ? 503 : body === null ? 404 : 200, { 'content-type': 'application/json' });
      res.end(JSON.stringify(mode === 'delayed-error' ? { detail: 'Fixture error' } : body ?? { detail: 'No fixture' }));
    } catch (error) { res.writeHead(500).end(String(error)); }
    return;
  }
  const upstream = http.request({ hostname: '127.0.0.1', port: nextPort, path: req.url, method: req.method, headers: { ...req.headers, host: `127.0.0.1:${nextPort}` } }, (response) => {
    res.writeHead(response.statusCode, response.headers);
    response.pipe(res);
  });
  upstream.on('error', () => { if (!res.headersSent) res.writeHead(502); res.end('Next unavailable'); });
  req.pipe(upstream);
});
server.listen(0, '127.0.0.1', () => console.log(`QA proxy http://127.0.0.1:${server.address().port} (down probe ${downPort})`));
