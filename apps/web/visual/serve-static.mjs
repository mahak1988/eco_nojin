#!/usr/bin/env node
/**
 * Serves the built Storybook over plain HTTP, with no dependency.
 *
 * The visual-regression gate runs against a *static* build rather than
 * `storybook dev`. Two reasons, both about the environment this repository is
 * actually built in: `storybook dev` compiles every story on request, so a
 * screenshot taken from it measures the dev server's timing as much as the
 * design, and it needs a running Node process for the length of every capture.
 * A static build is a directory of files, it is what a reviewer would deploy,
 * and it can be served by anything — including this, which is forty lines of
 * `node:http` and therefore cannot be broken by a package upgrade in a network
 * this build is not guaranteed to have.
 *
 * Usage:  node visual/serve-static.mjs [root] [port]
 */
import { createReadStream, existsSync, statSync } from 'node:fs';
import { createServer } from 'node:http';
import { extname, join, normalize, resolve } from 'node:path';

const ROOT = resolve(process.argv[2] ?? 'storybook-static');
const PORT = Number(process.argv[3] ?? 6007);

const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.woff2': 'font/woff2',
  '.woff': 'font/woff',
  '.ttf': 'font/ttf',
  '.ico': 'image/x-icon',
  '.webmanifest': 'application/manifest+json',
  '.map': 'application/json; charset=utf-8',
};

if (!existsSync(ROOT)) {
  console.error(`No static build at ${ROOT}. Run "pnpm build-storybook" first.`);
  process.exit(2);
}

const server = createServer((request, response) => {
  const url = new URL(request.url ?? '/', `http://localhost:${PORT}`);
  // `normalize` collapses `..` before the prefix test, so a request cannot climb
  // out of the build directory.
  const requested = normalize(decodeURIComponent(url.pathname)).replace(/^([/\\])+/, '');
  let file = join(ROOT, requested);
  if (!file.startsWith(ROOT)) {
    response.writeHead(403).end('Forbidden');
    return;
  }
  if (!existsSync(file) || statSync(file).isDirectory()) file = join(ROOT, 'index.html');
  if (!existsSync(file)) {
    response.writeHead(404).end('Not found');
    return;
  }
  response.writeHead(200, {
    'Content-Type': TYPES[extname(file)] ?? 'application/octet-stream',
    // Fonts are immutable and content-hashed by name; everything else must not
    // be cached or a stale build keeps answering.
    'Cache-Control': file.endsWith('.woff2') ? 'public, max-age=31536000, immutable' : 'no-store',
  });
  createReadStream(file).pipe(response);
});

server.listen(PORT, () => {
  console.log(`static storybook: http://localhost:${PORT}/  (root: ${ROOT})`);
});
