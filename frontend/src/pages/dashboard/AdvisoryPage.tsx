/** Advisory dashboard page — AI-powered farming advice with RAG grounding.
 * Uses POST /api/v1/ai/advise (RAG → NLG pipeline). */

import { useBilingual } from '../../hooks/useBilingual';
import Seo from '../../components/ui/Seo';
import PageHeader from '../../components/sections/PageHeader';
import AdvisoryRunner from '../../components/dashboard/AdvisoryRunner';
import Reveal from '../../components/ui/Reveal';
import SectionHeading from '../../components/ui/SectionHeading';

export default function AdvisoryPage() {
  const { t, fa } = useBilingual();

  return (
    <>
      <Seo title={`${fa('مشاوره کشاورزی هوشمند', 'AI Farm Advisory')} | ${t.brand.name}`} description={fa('مشاوره مبتنی بر داده MRV و RAG برای کشاورزان', 'Data-driven advisory for farmers')} path="/dashboard/advisory" />
      <PageHeader
        kicker={fa('ابزارهای هوشمند', 'Smart Tools')}
        title={fa('مشاوره کشاورزی هوشمند', 'AI Farm Advisory')}
        lead={fa(
          'پاسخ‌هایی مبتنی بر مستندات علمی و شاخص‌های ماهواره‌ای — با ارجاع صادقانه به منابع.',
          'Evidence-based recommendations with honest source attribution.',
        )}
      />

      <section className="px-4 py-12 sm:px-6" id="advisory">
        <div className="mx-auto flex max-w-6xl flex-col gap-8">
          <Reveal>
            <div className="mx-auto max-w-3xl text-center">
              <SectionHeading
                kicker={fa('چگونه کار می‌کند؟', 'How it works')}
                title={fa('RAG + NLG', 'Retrieval-Augmented Generation')}
                lead={fa(
                  'سیستم ابتدا سؤال شما را در دانشنامهٔ FAO و مدل‌های علمی جستجو می‌کند، سپس با استفاده از مدل زبانی پاسخی مبتنی بر شواهد تولید می‌کند. منابع همیشه ذکر می‌شوند.',
                  'The system first searches your question in the FAO knowledge base and scientific models, then generates an evidence-based response using language models. Sources are always cited.',
                )}
              />
            </div>
          </Reveal>

          <Reveal delay={0.1}>
            <AdvisoryRunner />
          </Reveal>
        </div>
      </section>
    </>
  );
}
