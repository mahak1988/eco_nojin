'use client';

import { useState } from 'react';
import { useFormContext, useFieldArray } from 'react-hook-form';
import { useTranslations } from 'next-intl';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { type Step3Input, type TrusteeInput } from '@/lib/validation/bazaar-establishment';

const REQUIRED_TRUSTEES = 5;

export function Step3Form({ locale }: { locale: string }) {
  const t = useTranslations('market.bazaarWizard.step3');
  const { register, control, watch } = useFormContext<Step3Input>();
  const { fields, append, remove } = useFieldArray({ control, name: 'trustees' });
  const trustees = watch('trustees');

  const [showAdd, setShowAdd] = useState(false);

  const isComplete = trustees.length === REQUIRED_TRUSTEES &&
    trustees.every(t => t.fullName && t.role && t.position);

  return (
    <div className="space-y-4" dir={locale === 'fa' || locale === 'ar' ? 'rtl' : 'ltr'}>
      <div className="flex items-center justify-between">
        <h3 className="font-medium text-ink">{t('foundingBoard')}</h3>
{fields.length < REQUIRED_TRUSTEES && (
            <Button variant="ghost" size="sm" onClick={() => setShowAdd(true)}>
              + {t('addTrustee')}
            </Button>
          )}
      </div>

      <div className="grid gap-4">
        {fields.map((field, index) => (
          <Card key={field.id} className="p-4">
            <div className="flex items-start justify-between gap-4 mb-3">
              <h4 className="font-medium text-ink">
                {t('trustee', { number: index + 1 })}
                <span className="text-sm text-ink-soft ml-2">({t('position')} {field.position})</span>
              </h4>
              {fields.length > 1 && (
                <Button variant="ghost" size="sm" onClick={() => remove(index)}>
                  {t('remove')}
                </Button>
              )}
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <Input
                label={t('fullName')}
                placeholder={t('fullNamePlaceholder')}
                {...register(`trustees.${index}.fullName`)}
              />
              <Input
                label={t('nationalId')}
                placeholder={t('nationalIdPlaceholder')}
                {...register(`trustees.${index}.nationalId`)}
              />
              <Input
                label={t('role')}
                placeholder={t('rolePlaceholder')}
                {...register(`trustees.${index}.role`)}
              />
              <Input
                label={t('position')}
                type="number"
                min="1"
                max="5"
                placeholder={t('positionPlaceholder')}
                {...register(`trustees.${index}.position`, { valueAsNumber: true })}
              />
              <Input
                label={t('phone')}
                type="tel"
                placeholder={t('phonePlaceholder')}
                {...register(`trustees.${index}.phone`)}
              />
              <Input
                label={t('email')}
                type="email"
                placeholder={t('emailPlaceholder')}
                {...register(`trustees.${index}.email`)}
              />
            </div>
          </Card>
        ))}
      </div>

      {fields.length < REQUIRED_TRUSTEES && showAdd && (
        <Card className="p-4 border-dashed">
          <div className="grid gap-3 sm:grid-cols-2">
            <Input
              label={t('fullName')}
              placeholder={t('fullNamePlaceholder')}
              {...register(`trustees.${fields.length}.fullName`)}
              autoFocus
            />
            <Input
              label={t('nationalId')}
              placeholder={t('nationalIdPlaceholder')}
              {...register(`trustees.${fields.length}.nationalId`)}
            />
            <Input
              label={t('role')}
              placeholder={t('rolePlaceholder')}
              {...register(`trustees.${fields.length}.role`)}
            />
            <Input
              label={t('position')}
              type="number"
              min="1"
              max="5"
              placeholder={t('positionPlaceholder')}
              {...register(`trustees.${fields.length}.position`, { valueAsNumber: true })}
            />
            <Input
              label={t('phone')}
              type="tel"
              placeholder={t('phonePlaceholder')}
              {...register(`trustees.${fields.length}.phone`)}
            />
            <Input
              label={t('email')}
              type="email"
              placeholder={t('emailPlaceholder')}
              {...register(`trustees.${fields.length}.email`)}
            />
          </div>
          <div className="flex gap-2 mt-4">
            <Button onClick={() => { append({ fullName: '', role: '', position: fields.length + 1 }); setShowAdd(false); }}>
              {t('saveTrustee')}
            </Button>
            <Button variant="ghost" onClick={() => setShowAdd(false)}>
              {t('cancel')}
            </Button>
          </div>
        </Card>
      )}

      {isComplete && (
        <div className="mt-4 p-3 bg-success/5 border border-success/20 rounded text-sm text-success">
          <strong>{t('boardComplete')}: </strong>
          {t('boardCompleteDesc')}
        </div>
      )}
    </div>
  );
}