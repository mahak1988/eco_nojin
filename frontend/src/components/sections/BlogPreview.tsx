import { useLang } from '../../i18n/LanguageContext';
import { Link } from 'react-router-dom';
import Reveal from '../ui/Reveal';
import { getBlog } from '../../content/contentHelpers';

/** Preview of latest 3 blog posts on HomePage. */
export default function BlogPreview() {
  const { lang } = useLang();
  const blog = getBlog(lang);

  const posts = blog?.posts?.slice(0, 3) ?? [];

  if (posts.length === 0) return null;

  return (
    <section className="px-4 py-16 sm:px-6 lg:py-24" id="blog-preview" aria-labelledby="blog-preview-heading">
      <div className="mx-auto max-w-6xl">
        <div className="flex flex-col items-start gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="mb-2 text-sm font-extrabold text-[var(--color-leaf-400)]">{blog?.kicker ?? 'بلاگ'}</p>
            <h2 id="blog-preview-heading" className="text-3xl font-extrabold text-[var(--color-night-100)] sm:text-4xl">
              {lang === 'fa' ? 'آخرین مقالات' : 'Latest Posts'}
            </h2>
          </div>
          <Link
            to="/blog"
            className="text-sm font-bold text-[var(--color-leaf-300)] hover:text-[var(--color-leaf-200)] transition-colors"
          >
            {lang === 'fa' ? 'همه مقالات →' : 'All posts →'}
          </Link>
        </div>

        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {posts.map((post, index) => (
            <Reveal key={post.title} delay={index * 0.08}>
              <Link
                to={`/blog#${post.title.replace(/\s+/g, '-').toLowerCase()}`}
                className="group flex flex-col gap-3 rounded-3xl glass glass-hover p-6 h-full"
              >
                <span className="text-xs font-bold text-[var(--color-aqua-300)]">{post.category}</span>
                <h3 className="text-lg font-extrabold text-[var(--color-night-100)] group-hover:text-[var(--color-leaf-300)] transition-colors line-clamp-2">
                  {post.title}
                </h3>
                <p className="text-sm leading-6 text-[var(--color-night-200)]/60 line-clamp-3">{post.excerpt}</p>
                <span className="mt-auto text-xs text-[var(--color-night-200)]/40">{post.date}</span>
              </Link>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
