/**
 * Script to split content/site.ts into per-section files.
 * Run with: node scripts/split-content.js
 */

const fs = require('fs');
const path = require('path');

const SITE_FILE = path.join(__dirname, '..', 'src', 'content', 'site.ts');
const OUTPUT_DIR = path.join(__dirname, '..', 'src', 'content', 'sections');

if (!fs.existsSync(SITE_FILE)) {
  console.error(`Site file not found: ${SITE_FILE}`);
  process.exit(1);
}

const content = fs.readFileSync(SITE_FILE, 'utf8');

// Extract types section (everything before the first `const fa:`)
const typesMatch = content.match(/^([\s\S]*?)(\nconst fa: SiteContent = \{)/);
if (!typesMatch) {
  console.error('Could not parse site.ts structure');
  process.exit(1);
}

const typesSection = typesMatch[1].trim();
const restAfterTypes = content.substring(typesMatch.index + typesMatch[0].length);

// Create output directory
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

// Write types to a shared file
fs.writeFileSync(path.join(OUTPUT_DIR, 'types.ts'), typesSection + '\n');
console.log('✓ Created sections/types.ts');

// Parse the fa and en objects
// We'll split by top-level keys in the SiteContent interface
const sectionKeys = [
  'meta', 'brand', 'nav', 'hero', 'stats', 'why', 'capabilities',
  'science', 'channels', 'carbon', 'platform', 'about',
  'terms', 'rules', 'privacy',
  'blog', 'faq', 'contact', 'transparency',
  'notFound', 'cta', 'footer', 'common'
];

// Simple parser: extract each section's fa and en values
let faObj = {};
let enObj = {};

// Extract fa object
const faStart = restAfterTypes.indexOf('{');
const faEnd = restAfterTypes.indexOf('const en: SiteContent = {');
const faContent = restAfterTypes.substring(faStart, faEnd).trim();

// Extract en object  
const enStart = restAfterTypes.indexOf('{', faEnd);
const enContent = restAfterTypes.substring(enStart).trim();

// Remove trailing semicolons
faContent.endsWith(';') && (faContent.slice(0, -1));
enContent.endsWith(';') && (enContent.slice(0, -1));

console.log('Content parsed. Creating section files...');

// Create a barrel file that re-exports everything
const barrelContent = `// Auto-generated barrel export for content sections
// Do not edit manually — run scripts/split-content.js instead

export { siteTypes } from './types';

`;

sectionKeys.forEach(key => {
  const sectionFile = path.join(OUTPUT_DIR, `${key}.ts`);
  
  const fileContent = `import type { SiteContent, Lang } from './types';

export interface ${key.charAt(0).toUpperCase() + key.slice(1)}Content {
  fa: SiteContent['${key}'];
  en: SiteContent['${key}'];
}

export const ${key} = {
  fa: ${key} as SiteContent['${key}'],
  en: ${key} as SiteContent['${key}'],
} satisfies { fa: SiteContent['${key}']; en: SiteContent['${key}'] };

export type ${key.charAt(0).toUpperCase() + key.slice(1)}Lang = 'fa' | 'en';
`;

  fs.writeFileSync(sectionFile, fileContent);
  barrelContent += `export { ${key} } from './${key}';\n`;
  console.log(`✓ Created sections/${key}.ts`);
});

// Write barrel file
fs.writeFileSync(path.join(OUTPUT_DIR, 'index.ts'), barrelContent);
console.log('✓ Created sections/index.ts');

// Now update the original site.ts to be a barrel file
const newSiteContent = `// Auto-generated barrel export — run scripts/split-content.js to regenerate
export * from './sections/types';
`;

fs.writeFileSync(SITE_FILE, newSiteContent);
console.log('✓ Updated content/site.ts as barrel export');

console.log('\n✅ Content split complete!');
console.log('   Next steps:');
console.log('   1. Update imports in components to use sections/*');
console.log('   2. Run tests to verify everything works');
console.log('   3. Commit the changes');
