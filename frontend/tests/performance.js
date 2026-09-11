import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

async function runCommand(command, args, cwd = process.cwd()) {
  return new Promise((resolve, reject) => {
    console.log(`Running: ${command} ${args.join(' ')}`);
    
    const process = spawn(command, args, { cwd, shell: true });
    
    let stdout = '';
    let stderr = '';
    
    process.stdout.on('data', (data) => {
      stdout += data.toString();
      console.log(data.toString());
    });
    
    process.stderr.on('data', (data) => {
      stderr += data.toString();
    });
    
    process.on('close', (code) => {
      if (code === 0) {
        resolve({ stdout, stderr, code });
      } else {
        reject(new Error(`Command failed with code ${code}: ${stderr}`));
      }
    });
  });
}

function getDirSize(dirPath) {
  let size = 0;
  const files = fs.readdirSync(dirPath);
  
  for (const file of files) {
    const filePath = path.join(dirPath, file);
    const stat = fs.statSync(filePath);
    
    if (stat.isDirectory()) {
      size += getDirSize(filePath);
    } else {
      size += stat.size;
    }
  }
  
  return size;
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function analyzeBundle(distDir) {
  const assetsDir = path.join(distDir, 'assets');
  const files = fs.readdirSync(assetsDir);
  
  console.log('\n📦 Bundle Analysis:\n');
  
  let totalSize = 0;
  const chunks = [];
  
  for (const file of files) {
    const filePath = path.join(assetsDir, file);
    const stat = fs.statSync(filePath);
    
    if (stat.isFile() && (file.endsWith('.js') || file.endsWith('.css'))) {
      chunks.push({
        file,
        size: stat.size,
        sizeFormatted: formatBytes(stat.size)
      });
      totalSize += stat.size;
    }
  }
  
  // Sort by size
  chunks.sort((a, b) => b.size - a.size);
  
  // Show top 5 largest files
  console.log('Top 5 Largest Files:');
  chunks.slice(0, 5).forEach((chunk, i) => {
    console.log(`  ${i + 1}. ${chunk.file}: ${chunk.sizeFormatted}`);
  });
  
  console.log(`\n📊 Total Bundle Size: ${formatBytes(totalSize)}`);
  
  // Performance thresholds
  const totalMB = totalSize / (1024 * 1024);
  
  if (totalMB > 1) {
    console.log('⚠️  Bundle exceeds 1MB - consider code splitting');
  } else if (totalMB > 0.5) {
    console.log('⚠️  Bundle is moderate size - monitor for growth');
  } else {
    console.log('✅ Bundle size is optimal');
  }
  
  return { totalSize, totalMB, chunks };
}

async function main() {
  console.log('🚀 Starting Performance Analysis...\n');
  
  const distDir = path.join(__dirname, '..', 'dist');
  
  try {
    // Step 1: Build the project
    console.log('Step 1: Building project...');
    await runCommand('pnpm', ['run', 'build'], process.cwd());
    
    // Step 2: Analyze the bundle
    if (fs.existsSync(distDir)) {
      console.log('\nStep 2: Analyzing bundle...');
      const analysis = analyzeBundle(distDir);
      
      // Save report
      const report = {
        timestamp: new Date().toISOString(),
        totalSize: analysis.totalSize,
        totalMB: analysis.totalMB,
        chunks: analysis.chunks
      };
      
      const reportDir = path.join(__dirname, '..', 'tests', 'reports');
      if (!fs.existsSync(reportDir)) {
        fs.mkdirSync(reportDir, { recursive: true });
      }
      
      const reportPath = path.join(reportDir, 'performance.json');
      fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
      console.log(`\n✅ Performance report saved to: ${reportPath}`);
    } else {
      console.log('❌ Build directory not found - check build process');
    }
  } catch (error) {
    console.error('❌ Build failed:', error.message);
    process.exit(1);
  }
  
  console.log('\n✅ Performance analysis complete!');
}

main().catch(console.error);