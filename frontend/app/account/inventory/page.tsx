// frontend/app/account/inventory/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth-context';
import { useI18n } from '@/lib/i18n-context';
import { useTheme } from '@/lib/theme-context';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Package, Search, Plus, Edit3, Trash2 } from 'lucide-react';

interface Material {
  id: number;
  name: string;
  category: 'seed' | 'fertilizer' | 'pesticide' | 'tool' | 'other';
  quantity: number;
  unit: string; // e.g., kg, liters, units
  expiry_date?: string; // Optional, mainly for chemicals/seeds
  farm_id: number; // Associated farm
}

export default function InventoryPage() {
  const { user, token } = useAuth();
  const { t } = useI18n();
  const { colors } = useTheme();
  const [materials, setMaterials] = useState<Material[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const fetchMaterials = async () => {
      try {
        // const res = await apiClient.get('/api/v1/materials');
        // setMaterials(res.data);
        // Mock data for demonstration
        setMaterials([
          { id: 1, name: 'Wheat Seeds', category: 'seed', quantity: 250, unit: 'kg', farm_id: 1 },
          { id: 2, name: 'Organic Fertilizer', category: 'fertilizer', quantity: 500, unit: 'kg', farm_id: 1 },
          { id: 3, name: 'Herbicide A', category: 'pesticide', quantity: 25, unit: 'liters', expiry_date: '2024-05-01', farm_id: 1 },
          { id: 4, name: 'Tractor Plow', category: 'tool', quantity: 1, unit: 'unit', farm_id: 1 },
        ]);
      } catch (err) {
        setError('Failed to load inventory.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      fetchMaterials();
    }
  }, [token]);

  const filteredMaterials = materials.filter(m =>
    m.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    m.category.includes(searchTerm.toLowerCase())
  );

  if (!user) {
    return (
      <div className="container mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <Card>
          <CardContent className="p-6 text-center text-muted-foreground">
            {t('common_please_log_in')}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <Card className="bg-red-50 border-red-200">
          <CardContent className="p-6 text-center text-red-700 flex items-center justify-center">
            <Package className="h-5 w-5 mr-2" />
            {error}
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
        <h1 className="text-3xl font-bold">{t('inventory_title')}</h1>
        <Button>
          <Plus className="mr-2 h-4 w-4" /> {t('inventory_add_item')}
        </Button>
      </div>

      <div className="flex items-center py-4">
        <Input
          placeholder={t('inventory_search_placeholder')}
          value={searchTerm}
          onChange={(event) => setSearchTerm(event.target.value)}
          className="max-w-sm"
        />
        <Button variant="outline" size="icon" className="ml-2">
          <Search className="h-4 w-4" />
        </Button>
      </div>

      {loading ? (
        <div className="space-y-4">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredMaterials.map((material) => (
            <Card key={material.id} style={{ backgroundColor: colors.cardBg, borderColor: colors.border }}>
              <CardHeader>
                <CardTitle className="flex justify-between items-start">
                  <span>{material.name}</span>
                  <Badge variant="outline">{t(`inventory_category_${material.category}`)}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{material.quantity} {material.unit}</p>
                {material.expiry_date && (
                  <p className="text-sm text-muted-foreground mt-1">{t('inventory_expiry')}: {new Date(material.expiry_date).toLocaleDateString()}</p>
                )}
                <div className="flex space-x-2 mt-4">
                  <Button variant="outline" size="sm">
                    <Edit3 className="h-4 w-4 mr-2" />
                    {t('common_edit')}
                  </Button>
                  <Button variant="outline" size="sm" className="text-red-500 hover:text-red-700">
                    <Trash2 className="h-4 w-4 mr-2" />
                    {t('common_delete')}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}