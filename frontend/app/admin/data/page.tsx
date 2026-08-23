// frontend/app/admin/data/page.tsx
'use client';

import { useAuth } from '@/lib/auth-context';
import { useI18n } from '@/lib/i18n-context';
import { useTheme } from '@/lib/theme-context';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Upload, Download, DatabaseBackup } from 'lucide-react';

export default function AdminDataPage() {
  const { user, token } = useAuth();
  const { t } = useI18n();
  const { colors } = useTheme();

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

  const handleUpload = () => {
    // Implement upload logic
    console.log('Trigger upload dialog');
  };

  const handleDownload = () => {
    // Implement download logic
    console.log('Trigger download');
  };

  const handleBackup = () => {
    // Implement backup logic
    console.log('Initiate backup');
  };

  return (
    <div className="container mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <h1 className="text-3xl font-bold mb-6">{t('admin_data_management_title')}</h1>
      <p className="mb-8 text-muted-foreground">{t('admin_data_management_description')}</p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card style={{ backgroundColor: colors.cardBg, borderColor: colors.border }}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5" />
              {t('admin_upload_data')}
            </CardTitle>
            <CardDescription>{t('admin_upload_data_desc')}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={handleUpload} className="w-full">{t('admin_select_files')}</Button>
          </CardContent>
        </Card>

        <Card style={{ backgroundColor: colors.cardBg, borderColor: colors.border }}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Download className="h-5 w-5" />
              {t('admin_download_data')}
            </CardTitle>
            <CardDescription>{t('admin_download_data_desc')}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={handleDownload} variant="outline" className="w-full">{t('admin_export')}</Button>
          </CardContent>
        </Card>

        <Card style={{ backgroundColor: colors.cardBg, borderColor: colors.border }}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <DatabaseBackup className="h-5 w-5" />
              {t('admin_backup_data')}
            </CardTitle>
            <CardDescription>{t('admin_backup_data_desc')}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={handleBackup} variant="secondary" className="w-full">{t('admin_run_backup')}</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}