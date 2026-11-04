import { readFileSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';
const hashes = JSON.parse(readFileSync('gptaudits/assets/magnifier-2026-11-03/original-sha256.json', 'utf8'));
function valid(bytes, digest) { return createHash('sha256').update(bytes).digest('hex') === digest; }
for (const [name, digest] of Object.entries(hashes)) {
  const bytes = readFileSync(`frontend/src/shared/assets/images/icons/${name}`);
  assert(valid(bytes, digest));
  assert(!valid(Buffer.from('changed asset'), digest));
  assert(!existsSync(name));
}
for (const path of ['frontend/src/widgets/Header/ui/Header.tsx','frontend/src/widgets/Header/ui/HeaderSearch.tsx','frontend/src/app/search/_components/SearchInput.tsx','frontend/src/widgets/authorizedHome/ui/QuickAccess.tsx']) {
  const source = readFileSync(path, 'utf8');
  assert(source.includes('<SearchIcon'));
  assert(!/<circle cx="11" cy="11"/.test(source));
}
console.log('MAGNIFIER_ASSETS_OK');
