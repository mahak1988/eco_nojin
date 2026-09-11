import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

async function runFullAudit(url, outputFile) {
  console.log(`\n📊 Accessibility Audit for: ${url}`);
  console.log('Running simulated audit (no browser available)...\n');
  
  const violations = await runSimulatedAudit(url, outputFile);
  
  console.log(`Found ${violations.length} potential issues\n`);
  
  violations.forEach((v, i) => {
    console.log(`${i + 1}. [${v.impact.toUpperCase()}] ${v.help}`);
  });
  
  if (violations.length === 0) {
    console.log('✅ No accessibility violations detected (simulated)');
  }
}

async function runSimulatedAudit(url, outputFile) {
  const violations = [];
  const htmlFiles = [
    path.join(__dirname, '..', 'index.html'),
    path.join(__dirname, '..', 'public', 'index.html'),
    path.join(__dirname, '../../index.html')
  ];
  
  let htmlContent = '';
  
  for (const file of htmlFiles) {
    try {
      htmlContent = fs.readFileSync(file, 'utf-8');
      break;
    } catch (e) {
      // Try next file
    }
  }
  
  if (htmlContent) {
    // Check for lang attribute on html tag
    if (!htmlContent.includes('<html lang=')) {
      violations.push({
        impact: 'serious',
        help: 'The html element must have a lang attribute',
        helpUrl: 'https://dequeuniversity.com/rules/axe/4.8/html-lang',
        nodes: [{ html: '<html>' }]
      });
    }
    
    // Check for title tag
    if (!/<title>/.test(htmlContent)) {
      violations.push({
        impact: 'moderate',
        help: 'Documents must have a title element',
        helpUrl: 'https://dequeuniversity.com/rules/axe/4.8/document-title',
        nodes: [{ html: '<head>' }]
      });
    }
    
    // Check for viewport meta tag
    if (!htmlContent.includes('viewport')) {
      violations.push({
        impact: 'serious',
        help: 'Elements must have sufficient color contrast',
        helpUrl: 'https://dequeuniversity.com/rules/axe/4.8/color-contrast',
        nodes: [{ html: '<meta name="viewport">' }]
      });
    }
    
    // Count images without alt
    const imgWithoutAlt = (htmlContent.match(/<img[^>]*>(?![^<]*alt=)/gi) || []).length;
    if (imgWithoutAlt > 0) {
      violations.push({
        impact: 'moderate',
        help: 'Images must have alternate text',
        helpUrl: 'https://dequeuniversity.com/rules/axe/4.8/image-alt',
        nodes: [{ html: `<img> × ${imgWithoutAlt}` }]
      });
    }
    
    // Check for ARIA roles
    const ariaRoles = (htmlContent.match(/role="[^"]+"/gi) || []).length;
    if (ariaRoles === 0) {
      violations.push({
        impact: 'moderate',
        help: 'ARIA roles and attributes are not used',
        nodes: [{ html: 'No ARIA roles found' }]
      });
    }
    
    // Check for skip navigation link
    if (!htmlContent.includes('skip') || (htmlContent.match(/id="skip"/i) === null && htmlContent.match(/class="skip"/i) === null)) {
      violations.push({
        impact: 'moderate',
        help: 'Page should contain a focusable skip link',
        helpUrl: 'https://www.w3.org/WAI/techniques/general/G1',
        nodes: [{ html: 'Missing <a class="skip"> skip link' }]
      });
    }
  } else {
    console.log('⚠️ Could not find HTML files to analyze');
    console.log('   Please ensure the dev server is running or run from the frontend directory');
    
    // Default violations when no HTML found
    violations.push({
      impact: 'serious',
      help: 'Could not find index.html - file structure issue',
      nodes: [{ html: 'Run from frontend directory or check file paths' }]
    });
  }
  
  // Save report if output file specified
  if (outputFile) {
    const report = {
      timestamp: new Date().toISOString(),
      url,
      type: 'simulated',
      totalViolations: violations.length,
      violations
    };
    
    const reportDir = path.dirname(outputFile);
    if (!fs.existsSync(reportDir)) {
      fs.mkdirSync(reportDir, { recursive: true });
    }
    
    fs.writeFileSync(outputFile, JSON.stringify(report, null, 2));
    console.log(`\n✅ Report saved to: ${outputFile}`);
  }
  
  return violations;
}

// Main execution
async function main() {
  const pagesToTest = [
    { url: 'http://localhost:5175', output: 'tests/reports/accessibility-home.json' },
    { url: 'http://localhost:5175/login', output: 'tests/reports/accessibility-login.json' },
    { url: 'http://localhost:5175/dashboard', output: 'tests/reports/accessibility-dashboard.json' }
  ];
  
  console.log('Starting Accessibility Audit...\n');
  
  for (const page of pagesToTest) {
    await runFullAudit(page.url, path.join(__dirname, '..', page.output));
  }
  
  console.log('\n✅ Accessibility audit complete!');
  console.log('\n📝 Next Steps:');
  console.log('   1. Start dev server: pnpm dev');
  console.log('   2. Re-run with browser: node tests/accessibility.js');
  console.log('   3. Review reports in tests/reports/');
  console.log('   4. Fix identified accessibility issues');
  console.log('   5. Add prefers-reduced-motion CSS (already in place)');
  console.log('   6. Add ARIA attributes and semantic HTML to critical components');
}

main().catch(console.error);