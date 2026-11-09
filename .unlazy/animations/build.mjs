import { mkdtemp, readdir, realpath, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { spawn } from 'node:child_process';
const root = resolve('frontend');
const dest = await mkdtemp(join(tmpdir(), 'bscout-animation-build-'));
const allowed = /^(src|public|node_modules|package(?:-lock)?\.json|next\.config\.mjs|next-env\.d\.ts|tsconfig\.json|tailwind\.config\.ts|postcss\.config\.mjs|\.eslintrc(?:\.json|\.js|\.cjs)?)$/;
for (const name of await readdir(root)) {
  if (!allowed.test(name)) continue;
  const copy = spawn('/bin/cp', ['-R', join(root, name), join(dest, name)], { stdio: 'inherit' });
  const status = await new Promise((resolveExit, reject) => {
    copy.on('error', reject);
    copy.on('exit', (code) => resolveExit(code ?? 1));
  });
  if (status !== 0) throw new Error(`Copy failed for ${name}: ${status}`);
}
const nextBin = await realpath(join(dest, 'node_modules/.bin/next'));
if (!nextBin.startsWith(`${await realpath(dest)}/`)) throw new Error(`Next binary escapes isolated build: ${nextBin}`);
await writeFile(resolve('.unlazy/animations/build-path.txt'), `${dest}\n`);
console.log(`Isolated frontend: ${dest}`);
const child = spawn(process.execPath, [join(dest, 'node_modules/next/dist/bin/next'), 'build'], { cwd: dest, stdio: 'inherit', env: { ...process.env, NEXT_TELEMETRY_DISABLED: '1' } });
const code = await new Promise((resolveExit, reject) => {
  child.on('error', reject);
  child.on('exit', (status) => resolveExit(status ?? 1));
});
process.exitCode = code;
