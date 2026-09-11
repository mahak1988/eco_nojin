/** HTML sanitizer for user-generated content.
 *
 * Uses DOMPurify for production-grade sanitization.
 * Falls back to a basic regex-based sanitizer if DOMPurify is not available.
 */

import DOMPurify from 'dompurify';

const ALLOWED_TAGS = [
  'b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li',
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'code', 'pre',
];

const ALLOWED_ATTR = ['href', 'title', 'target', 'rel'];

export function sanitizeHtml(dirty: string): string {
  if (typeof window === 'undefined') {
    return dirty;
  }

  try {
    return DOMPurify.sanitize(dirty, {
      ALLOWED_TAGS,
      ALLOWED_ATTR,
      ALLOWED_URI_REGEXP: /^(?:https?|mailto|tel):/i,
    });
  } catch {
    // Fallback: strip script tags and event handlers
    return dirty
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
      .replace(/\s(on\w+)=/gi, ' ');
  }
}
