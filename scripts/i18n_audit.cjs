#!/usr/bin/env node
/* i18n key audit: compares leaf keys across all locale files, and checks
   parity between the paraglide source dir and the compiled dir. */
const fs = require('fs');
const path = require('path');

function leafKeys(obj, prefix = '') {
  const out = [];
  if (Array.isArray(obj)) {
    obj.forEach((item, i) => out.push(...leafKeys(item, `${prefix}[${i}]`)));
    return out;
  }
  if (obj && typeof obj === 'object') {
    for (const k of Object.keys(obj)) {
      const v = obj[k];
      const key = prefix ? `${prefix}.${k}` : k;
      if (v && typeof v === 'object') out.push(...leafKeys(v, key));
      else out.push(key);
    }
  } else {
    out.push(prefix);
  }
  return out;
}

function audit(dir, baseLocale = 'en') {
  console.log(`\n=== ${dir} ===`);
  if (!fs.existsSync(dir)) { console.log('  (missing dir)'); return; }
  const files = fs.readdirSync(dir).filter(f => f.endsWith('.json') && f !== 'package.json');
  const base = JSON.parse(fs.readFileSync(path.join(dir, `${baseLocale}.json`), 'utf8'));
  const baseKeys = leafKeys(base);
  const dedup = new Set(baseKeys);
  console.log(`base (${baseLocale}) leaf keys: raw=${baseKeys.length} deduped=${dedup.size}`);
  const sections = {};
  for (const k of dedup) {
    const top = k.split(/[.[]/)[0];
    sections[top] = (sections[top] || 0) + 1;
  }
  console.log('  sections:', Object.entries(sections).map(([k, v]) => `${k}=${v}`).join(', '));
  for (const f of files) {
    const loc = f.replace('.json', '');
    if (loc === baseLocale) continue;
    let j;
    try { j = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')); }
    catch (e) { console.log(`  ${loc}: PARSE ERROR ${e.message}`); continue; }
    const keys = leafKeys(j);
    const keySet = new Set(keys);
    const missing = [...dedup].filter(k => !keySet.has(k));
    const extra = keys.filter(k => !dedup.has(k));
    const empty = keys.filter(k => {
      let v = j;
      for (const part of k.split('.')) {
        if (v == null) break;
        const m = part.match(/^(.*?)\[(\d+)\]$/);
        if (m) { v = v[m[1]] != null ? v[m[1]][Number(m[2])] : undefined; }
        else if (part.startsWith('[')) { v = v[Number(part.slice(1, -1))]; }
        else { v = v[part]; }
      }
      return v === '' || v === null || v === undefined;
    });
    const status = missing.length || empty.length ? 'FAIL' : 'OK';
    console.log(`  ${loc}: keys=${keys.length} missing=${missing.length} extra=${extra.length} empty=${empty.length} -> ${status}`);
    if (missing.length) console.log(`    missing: ${missing.slice(0, 15).join(', ')}${missing.length > 15 ? ` (+${missing.length - 15})` : ''}`);
    if (empty.length) console.log(`    empty: ${empty.slice(0, 15).join(', ')}${empty.length > 15 ? ` (+${empty.length - 15})` : ''}`);
  }
}

// Dump villageHub section (en + fa) for translation work
const path = require('path');
function leafKeys(obj, prefix = '') {
  const out = [];
  if (Array.isArray(obj)) { obj.forEach((v, i) => out.push(...leafKeys(v, `${prefix}[${i}]`))); return out; }
  if (obj && typeof obj === 'object') {
    for (const k of Object.keys(obj)) {
      const key = prefix ? `${prefix}.${k}` : k;
      const v = obj[k];
      if (v && typeof v === 'object') out.push(...leafKeys(v, key)); else out.push(key);
    }
  }
  return out;
}
function getVal(obj, key) {
  let v = obj;
  for (const part of key.split('.')) {
    if (v == null) return undefined;
    const m = part.match(/^(.*?)\[(\d+)\]$/);
    v = m ? (v[m[1]] || [])[Number(m[2])] : v[part];
  }
  return v;
}
const CANON = 'd:/eco_nojin/frontend/project.inlang/messages';
const en = JSON.parse(fs.readFileSync(path.join(CANON, 'en.json'), 'utf8'));
const fa = JSON.parse(fs.readFileSync(path.join(CANON, 'fa.json'), 'utf8'));
const keys = leafKeys(en).filter(k => k.startsWith('villageHub.'));
for (const k of keys) {
  console.log(`${k}\n  en: ${JSON.stringify(getVal(en, k))}\n  fa: ${JSON.stringify(getVal(fa, k))}`);
}
console.log('total:', keys.length);


function leafKeys(obj, prefix = '') {
  const out = [];
  if (Array.isArray(obj)) { obj.forEach((v, i) => out.push(...leafKeys(v, `${prefix}[${i}]`))); return out; }
  if (obj && typeof obj === 'object') {
    for (const k of Object.keys(obj)) {
      const key = prefix ? `${prefix}.${k}` : k;
      const v = obj[k];
      if (v && typeof v === 'object') out.push(...leafKeys(v, key)); else out.push(key);
    }
  }
  return out;
}
function getVal(obj, key) {
  let v = obj;
  for (const part of key.split('.')) {
    if (v == null) return undefined;
    const m = part.match(/^(.*?)\[(\d+)\]$/);
    v = m ? (v[m[1]] || [])[Number(m[2])] : v[part];
  }
  return v;
}

const CANON = 'd:/eco_nojin/frontend/project.inlang/messages';
const GEN = 'd:/eco_nojin/frontend/src/paraglide/messages';
for (const loc of ['ar', 'es', 'fr', 'hi', 'fa']) {
  const c = JSON.parse(fs.readFileSync(path.join(CANON, `${loc}.json`), 'utf8'));
  const g = JSON.parse(fs.readFileSync(path.join(GEN, `${loc}.json`), 'utf8'));
  const keys = leafKeys(g);
  let same = 0, diff = 0, genEmpty = 0, canonEmptyForGenFull = 0;
  const diffSamples = [];
  for (const k of keys) {
    const gv = getVal(g, k), cv = getVal(c, k);
    if (gv === '' || gv == null) { genEmpty++; continue; }
    if (cv === '' || cv == null) { canonEmptyForGenFull++; continue; }
    if (gv === cv) same++; else { diff++; if (diffSamples.length < 3) diffSamples.push(`${k}: canon='${String(cv).slice(0, 40)}' gen='${String(gv).slice(0, 40)}'`); }
  }
  console.log(`${loc}: sharedNonEmpty same=${same} diff=${diff} | genEmpty=${genEmpty} | canonEmptyWhereGenHasValue=${canonEmptyForGenFull}`);
  diffSamples.forEach(s => console.log('   ' + s));
}

