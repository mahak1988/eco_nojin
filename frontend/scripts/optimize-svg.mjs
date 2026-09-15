import { optimize } from 'svgo';
import { readdirSync, statSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PUBLIC_DIR = join(__dirname, '..', 'public');

const config = {
  plugins: [
    { name: 'preset-default' },
    { name: 'removeDoctype' },
    { name: 'removeComments' },
    { name: 'inlineStyles' },
  ],
};

const svgs = [];

function collect(dir) {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    const stat = statSync(full);
    if (stat.isDirectory()) {
      collect(full);
    } else if (entry.endsWith('.svg')) {
      svgs.push(full);
    }
  }
}

collect(PUBLIC_DIR);
console.log(`Optimizing ${svgs.length} SVG files...`);

for (const svg of svgs) {
  try {
    const original = readFileSync(svg, 'utf8');
    const result = optimize(original, { path: svg, ...config });
    if (result.data && result.data !== original) {
      writeFileSync(svg, result.data);
      const saved = ((original.length - result.data.length) / original.length * 100).toFixed(1);
      console.log(`  ✓ ${svg.replace(__dirname + '/../', '')} (${saved}% smaller)`);
    }
  } catch (err) {
    console.error(`  ✗ ${svg}: ${err.message}`);
  }
}
console.log('Done.');
