// frontend/app/admin/settings/page.tsx
'use client';

import { useState } from 'react';
import { useAuth } from '@/lib/auth-context';
import { useI18n } from '@/lib/i18n-context';
import { useTheme } from '@/lib/theme-context';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Settings } from 'lucide-react';

export default function AdminSettingsPage() {
  const { user, token } = useAuth();
  const { t } = useI18n();
  const { colors } = useTheme();
  const [maintenanceMode, setMaintenanceMode] = useState(false);
  const [newApiKey, setNewApiKey] = useState('');
  const [smtpServer, setSmtpServer] = useState('smtp.example.com');

  const handleSave = () => {
    // Implement save logic
    console.log('Saving settings...');
    alert(t('admin_settings_saved'));
  };

  if (!user || user.role !== 'admin') {
    return (
      <div className="flex items-center justify-center h-[70vh]">
        <Card className="bg-red-50 border-red-200">
          <CardContent className="p-6 text-center text-red-700">
            {t('admin_access_denied')}
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <h1 className="text-3xl font-bold mb-6">{t('admin_settings_title')}</h1>

      <Card style={{ backgroundColor: colors.cardBg, borderColor: colors.border }}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            {t('admin_general_settings')}
          </CardTitle>
          <CardDescription>{t('admin_general_settings_desc')}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="maintenance-mode">{t('admin_maintenance_mode')}</Label>
              <p className="text-xs text-muted-foreground">{t('admin_maintenance_mode_desc')}</p>
            </div>
            <Switch
              id="maintenance-mode"
              checked={maintenanceMode}
              onCheckedChange={setMaintenanceMode}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="api-key">{t('admin_new_api_key')}</Label>
            <div className="flex">
              <Input
                id="api-key"
                type="password"
                value={newApiKey}
                onChange={(e) => setNewApiKey(e.target.value)}
                placeholder={t('admin_generate_new_key_placeholder')}
              />
              <Button variant="outline" className="ml-2">Generate</Button>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="smtp-server">{t('admin_smtp_server')}</Label>
            <Input
              id="smtp-server"
              type="text"
              value={smtpServer}
              onChange={(e) => setSmtpServer(e.target.value)}
              placeholder={t('admin_smtp_server_placeholder')}
            />
          </div>

          <Button onClick={handleSave} className="mt-4">{t('admin_save_settings')}</Button>
        </CardContent>
      </Card>
    </div>
  );
}