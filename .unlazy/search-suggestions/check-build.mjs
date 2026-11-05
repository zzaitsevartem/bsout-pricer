import {spawnSync} from 'node:child_process';
import {readFileSync,cpSync} from 'node:fs';
import path from 'node:path';
const target=readFileSync('.unlazy/search-suggestions/build-path.txt','utf8').trim();
cpSync('frontend/src',path.join(target,'src'),{recursive:true});
const result=spawnSync(process.execPath,['node_modules/next/dist/bin/next','build'],{cwd:target,stdio:'inherit'});
if(result.status!==0)process.exit(result.status??1);
console.log('FRONTEND_BUILD_VERIFIED');
