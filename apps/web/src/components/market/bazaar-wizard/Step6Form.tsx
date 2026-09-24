'use client';

import { useFormContext, useFieldArray } from 'react-hook-form';
import { useTranslations } from 'next-intl';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { type Step6Input, type SignatureInput } from '@/lib/validation/bazaar-establishment';

const PQ_ALGORITHMS = [
  { value: 'DILITHIUM2+ED25519', label: 'DILITHIUM2 + ED25519 (Sign)' },
  { value: 'KYBER512+X25519', label: 'KYBER512 + X25519 (KEM)' },
];

export function Step6Form({ locale }: { locale: string }) {
  const t = useTranslations('market.bazaarWizard.step6');
  const { register, control, watch } = useFormContext<Step6Input>();
  const { fields, append, remove } = useFieldArray({ control, name: 'signatures' });
  const signatures = watch('signatures');

  const trusteeCount = 5;
  const signedCount = signatures.length;

  return (
    <div className="space-y-4" dir={locale === 'fa' || locale === 'ar' ? 'rtl' : 'ltr'}>
      <div className="flex items-center justify-between">
        <h3 className="font-medium text-ink">{t('digitalSignatures')}</h3>
        <span className="text-sm text-ink-soft">
          {t('progress', { current: signedCount, total: trusteeCount })}
        </span>
      </div>

      <Card className="p-4">
        <p className="text-sm text-ink-soft mb-4">{t('description')}</p>

        <div className="grid gap-3 sm:grid-cols-2 mb-4">
          {PQ_ALGORITHMS.map(algo => (
            <label key={algo.value} className="inline-flex items-center gap-2 px-3 py-2 rounded border cursor-pointer hover:bg-surface-alt">
              <input type="radio" name="defaultAlgorithm" value={algo.value} />
              <span className="font-mono text-sm">{algo.label}</span>
            </label>
          ))}
        </div>

        <div className="grid gap-3">
          {fields.map((field, index) => (
            <Card key={field.id} className="p-4">
              <div className="flex items-start justify-between gap-4 mb-3">
                <h4 className="font-medium text-ink">
                  {t('signature', { number: index + 1 })}
                </h4>
                {fields.length > 1 && (
                  <Button variant="ghost" size="sm" onClick={() => remove(index)}>
                    {t('remove')}
                  </Button>
                )}
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <Input
                  label={t('trusteeId')}
                  placeholder={t('trusteeIdPlaceholder')}
                  {...register(`signatures.${index}.trusteeId`)}
                />
                <Input
                  label={t('stepNumber')}
                  type="number"
                  min="1"
                  max="10"
                  placeholder={t('stepNumberPlaceholder')}
                  {...register(`signatures.${index}.stepNumber`, { valueAsNumber: true })}
                />
                <Input
                  label={t('signatureHex')}
                  placeholder={t('signatureHexPlaceholder')}
                  className="font-mono text-sm"
                  {...register(`signatures.${index}.signatureHex`)}
                />
                <Input
                  label={t('pqPublicKeyHex')}
                  placeholder={t('pqPublicKeyHexPlaceholder')}
                  className="font-mono text-sm"
                  {...register(`signatures.${index}.pqPublicKeyHex`)}
                />
                <Input
                  label={t('ciphertextHex')}
                  placeholder={t('ciphertextHexPlaceholder')}
                  className="font-mono text-sm"
                  {...register(`signatures.${index}.ciphertextHex`)}
                />
                <Input
                  label={t('sharedSecretHex')}
                  placeholder={t('sharedSecretHexPlaceholder')}
                  className="font-mono text-sm"
                  {...register(`signatures.${index}.sharedSecretHex`)}
                />
                <Select
                  label={t('algorithm')}
                  {...register(`signatures.${index}.algorithm`)}
                >
                  <option value="DILITHIUM2+ED25519">DILITHIUM2 + ED25519</option>
                  <option value="KYBER512+X25519">KYBER512 + X25519</option>
                </Select>
                <Select
                  label={t('kemAlgorithm')}
                  {...register(`signatures.${index}.kemAlgorithm`)}
                >
                  <option value="KYBER512">KYBER512</option>
                  <option value="X25519">X25519</option>
                </Select>
              </div>
            </Card>
          ))}
        </div>

        {fields.length < trusteeCount && (
          <Button variant="ghost" onClick={() => append({
            trusteeId: '',
            stepNumber: 6,
            signatureHex: '',
            pqPublicKeyHex: '',
            algorithm: 'DILITHIUM2+ED25519',
            kemAlgorithm: 'KYBER512',
          })}>
            + {t('addSignature')}
          </Button>
        )}
      </Card>

      {signedCount >= trusteeCount && (
        <div className="mt-4 p-3 bg-success/5 border border-success/20 rounded text-sm text-success">
          <strong>{t('allSigned')}: </strong>
          {t('allSignedDesc')}
        </div>
      )}
    </div>
  );
}