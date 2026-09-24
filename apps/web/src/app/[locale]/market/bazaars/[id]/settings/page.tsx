'use client';

import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Textarea } from '@/components/ui/Textarea';
import { Switch } from '@/components/ui/Switch';

export default function BazaarSettingsPage() {
  const params = useParams();
  const locale = params.locale as string;
  const id = params.id as string;
  const bazaarId = id ?? '';
  const t = useTranslations('market.bazaarSettings');

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-3xl px-6 pb-12 pt-6">
        <header className="mb-8">
          <nav className="mb-4">
            <a
              href={`/${locale}/market/bazaars/${bazaarId}`}
              className="text-sm text-ink-soft hover:text-ink underline"
            >
              ← {locale === 'fa' ? 'بازگشت به بازارچه' : 'Back to Bazaar'}
            </a>
          </nav>
          <ProvenanceStamp source="bazaar-settings" label="بازارچه — تنظیمات">
            <h1 className="display text-3xl font-bold text-ink sm:text-4xl">
              {t('title', { id: bazaarId })}
            </h1>
          </ProvenanceStamp>
        </header>

        <Card className="mb-6">
          <p className="text-ink-soft">{t('description')}</p>
        </Card>

        <Card className="mb-6">
          <h3 className="font-medium text-ink mb-4 pb-3 border-b">{t('general')}</h3>
          <div className="space-y-4">
            <Input label={t('bazaarName')} placeholder={t('bazaarNamePlaceholder')} defaultValue="بازارچه نهادی مرکزی" />
            <Input label={t('bazaarCode')} placeholder={t('bazaarCodePlaceholder')} defaultValue="BZR-001" />
            <Textarea label={t('description')} placeholder={t('descriptionPlaceholder')} rows={3} defaultValue="بازارچه نهادی مرکزی شامل ۴۲ فروشگاه..." />
            <Select label={t('bazaarType')}>
              <option value="rural">{t('bazaarType.rural')}</option>
              <option value="inter_village">{t('bazaarType.interVillage')}</option>
              <option value="regional">{t('bazaarType.regional')}</option>
              <option value="specialty">{t('bazaarType.specialty')}</option>
            </Select>
            <div className="flex items-center justify-between">
              <span className="text-ink">{t('isActive')}</span>
              <Switch defaultChecked />
            </div>
          </div>
        </Card>

        <Card className="mb-6">
          <h3 className="font-medium text-ink mb-4 pb-3 border-b">{t('location')}</h3>
          <div className="space-y-4">
            <Input label={t('address')} placeholder={t('addressPlaceholder')} defaultValue="خراسان رضوی، ایران" />
            <div className="grid gap-4 sm:grid-cols-2">
              <Input label={t('latitude')} type="number" step="0.000001" defaultValue="36.2605" />
              <Input label={t('longitude')} type="number" step="0.000001" defaultValue="59.6168" />
            </div>
            <Input label={t('timezone')} placeholder={t('timezonePlaceholder')} defaultValue="Asia/Tehran" />
          </div>
        </Card>

        <Card className="mb-6">
          <h3 className="font-medium text-ink mb-4 pb-3 border-b">{t('operatingHours')}</h3>
          <div className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-3">
              <Select label={t('openDay')}>
                <option value="saturday">{t('day.saturday')}</option>
                <option value="sunday">{t('day.sunday')}</option>
                <option value="monday">{t('day.monday')}</option>
                <option value="tuesday">{t('day.tuesday')}</option>
                <option value="wednesday">{t('day.wednesday')}</option>
                <option value="thursday">{t('day.thursday')}</option>
                <option value="friday">{t('day.friday')}</option>
              </Select>
              <Input label={t('openTime')} type="time" defaultValue="08:00" />
              <Input label={t('closeTime')} type="time" defaultValue="20:00" />
            </div>
          </div>
        </Card>

        <Card className="mb-6">
          <h3 className="font-medium text-ink mb-4 pb-3 border-b">{t('notifications')}</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-ink">{t('emailNotifications')}</p>
                <p className="text-sm text-ink-soft">{t('emailNotificationsDesc')}</p>
              </div>
              <Switch defaultChecked />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-ink">{t('smsNotifications')}</p>
                <p className="text-sm text-ink-soft">{t('smsNotificationsDesc')}</p>
              </div>
              <Switch />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-ink">{t('pushNotifications')}</p>
                <p className="text-sm text-ink-soft">{t('pushNotificationsDesc')}</p>
              </div>
              <Switch defaultChecked />
            </div>
          </div>
        </Card>

        <Card className="mb-6">
          <h3 className="font-medium text-ink mb-4 pb-3 border-b">{t('advanced')}</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-ink">{t('maintenanceMode')}</p>
                <p className="text-sm text-ink-soft">{t('maintenanceModeDesc')}</p>
              </div>
              <Switch />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-ink">{t('requireApproval')}</p>
                <p className="text-sm text-ink-soft">{t('requireApprovalDesc')}</p>
              </div>
              <Switch defaultChecked />
            </div>
            <Input label={t('maxStores')} type="number" min="1" max="100" defaultValue="50" />
          </div>
        </Card>

        <div className="flex gap-3 justify-end">
          <Button variant="ghost">{t('cancel')}</Button>
          <Button>{t('saveChanges')}</Button>
        </div>
      </div>
    </main>
  );
}