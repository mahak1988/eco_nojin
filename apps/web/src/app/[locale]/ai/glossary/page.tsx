'use client';

import { useState, useMemo } from 'react';
import { useTranslations } from 'next-intl';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

interface GlossaryTerm {
  term: string;
  definition: string;
  category: string;
  related?: string[];
}

const GLOSSARY_DATA: GlossaryTerm[] = [
  { term: 'RAG', definition: 'Retrieval-Augmented Generation: A technique that combines information retrieval with text generation to provide grounded, source-cited answers.', category: 'Core' },
  { term: 'Embeddings', definition: 'Vector representations of text that capture semantic meaning, enabling similarity search and clustering.', category: 'Core' },
  { term: 'Provenance Stamp', definition: 'A visual indicator linking each AI response to its source documents, ensuring traceability and accountability.', category: 'Core' },
  { term: 'Hallucination', definition: 'When a language model generates plausible-sounding but factually incorrect or unsupported information.', category: 'Risks' },
  { term: 'Grounding', definition: 'The process of constraining model outputs to verified sources, reducing hallucination risk.', category: 'Core' },
  { term: 'Context Window', definition: 'The maximum amount of text (tokens) a model can process at once, limiting how much information can be referenced.', category: 'Technical' },
  { term: 'Token', definition: 'A unit of text (word, subword, or character) used by language models for processing; roughly 0.75 words per token in English.', category: 'Technical' },
  { term: 'Fine-tuning', definition: 'Adapting a pre-trained model on domain-specific data to improve performance on specialized tasks.', category: 'Technical' },
  { term: 'Prompt Engineering', definition: 'Designing input prompts to elicit desired behaviors and outputs from language models.', category: 'Technical' },
  { term: 'Agent', definition: 'An autonomous system that uses language models to plan, reason, and execute actions toward a goal.', category: 'Core' },
  { term: 'Multi-agent Orchestration', definition: 'Coordinating multiple specialized agents to solve complex tasks through collaboration.', category: 'Core' },
  { term: 'Tool Use', definition: 'The ability of a language model to invoke external functions (APIs, calculators, search) during reasoning.', category: 'Core' },
  { term: 'Temperature', definition: 'A sampling parameter controlling output randomness; lower values produce more deterministic responses.', category: 'Technical' },
  { term: 'Top-p Sampling', definition: 'Nucleus sampling that considers only the most probable tokens whose cumulative probability exceeds threshold p.', category: 'Technical' },
  { term: 'System Prompt', definition: 'A fixed instruction set that defines the model\'s role, behavior, and constraints for all interactions.', category: 'Technical' },
  { term: 'Guardrails', definition: 'Safety mechanisms that filter, validate, or constrain model outputs to prevent harmful or inaccurate responses.', category: 'Risks' },
  { term: 'Human-in-the-loop', definition: 'A design pattern where human review or approval is required for critical decisions or outputs.', category: 'Risks' },
  { term: 'Explainability', definition: 'The degree to which an AI system\'s decision-making process can be understood by humans.', category: 'Risks' },
  { term: 'Bias', definition: 'Systematic errors in model outputs that reflect societal biases present in training data.', category: 'Risks' },
  { term: 'Alignment', definition: 'The process of ensuring model behavior matches human values, intentions, and safety requirements.', category: 'Risks' },
];

const CATEGORIES = ['All', 'Core', 'Technical', 'Risks'];

export default function GlossaryPage() {
  const t = useTranslations('ai.glossary');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');

  const filteredTerms = useMemo(() => {
    return GLOSSARY_DATA.filter((term) => {
      const matchesSearch = term.term.toLowerCase().includes(searchQuery.toLowerCase()) ||
        term.definition.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesCategory = selectedCategory === 'All' || term.category === selectedCategory;
      return matchesSearch && matchesCategory;
    });
  }, [searchQuery, selectedCategory]);

  return (
    <main id="main" className="min-h-screen">
      <div className="mx-auto max-w-4xl px-4 py-10">
        <header className="mb-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title')}</h1>
          <p className="mt-3 text-ink-soft">{t('lead')}</p>
        </header>

        <Card density="compact" className="mb-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              <input
                type="search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t('searchPlaceholder')}
                className="w-full pl-10 pr-4 py-2 rounded-md border border-line bg-background text-ink focus:outline-none focus:ring-2 focus:ring-forest"
                aria-label={t('searchLabel')}
              />
            </div>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-4 py-2 rounded-md border border-line bg-background text-ink focus:outline-none focus:ring-2 focus:ring-forest"
              aria-label={t('categoryLabel')}
            >
              {CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>{t(`category.${cat.toLowerCase()}`)}</option>
              ))}
            </select>
          </div>
          <p className="mt-2 text-sm text-ink-soft">{t('resultsCount', { count: filteredTerms.length })}</p>
        </Card>

        <div className="space-y-3" role="list" aria-label={t('termsListLabel')}>
          {filteredTerms.length === 0 ? (
            <Card density="cozy" className="text-center py-8">
              <p className="text-ink-soft">{t('noResults')}</p>
            </Card>
          ) : (
            filteredTerms.map((term, index) => (
              <Card key={term.term} density="compact" className="group" role="listitem">
                <div className="flex flex-col sm:flex-row sm:items-start gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-4">
                      <h3 className="font-medium text-ink text-lg">{term.term}</h3>
                      <span className="px-2 py-0.5 text-xs rounded-full bg-forest/10 text-forest font-medium whitespace-nowrap shrink-0">
                        {t(`category.${term.category.toLowerCase()}`)}
                      </span>
                    </div>
                    <p className="mt-2 text-ink-soft">{term.definition}</p>
                    {term.related && term.related.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {term.related.map((rel, idx) => (
                          <Button key={idx} variant="ghost" size="sm" className="text-xs">
                            {rel}
                          </Button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      </div>
    </main>
  );
}