const allowedOfflinePaths = [/^\/api\/v1\/public\//];

export function isCacheablePublicRequest(url: URL, method: string, sameOrigin: boolean): boolean {
  return sameOrigin && method === 'GET' && !url.pathname.startsWith('/api/');
}

export function isAllowedOfflineMutation(path: string, method: string): boolean {
  return method === 'POST' && allowedOfflinePaths.some((pattern) => pattern.test(path));
}
