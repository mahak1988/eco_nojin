// frontend/app/admin/users/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth-context';
import { useI18n } from '@/lib/i18n-context';
import { useTheme } from '@/lib/theme-context';
import { DataTable } from '@/components/ui/data-table'; // Assume a generic table component exists
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Search, UserPlus, Eye, Edit, Trash2 } from 'lucide-react';

interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  last_login?: string;
}

export default function AdminUsersPage() {
  const { user, token } = useAuth();
  const { t } = useI18n();
  const { colors } = useTheme();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    // Simulate API call to fetch users
    const fetchUsers = async () => {
      // const res = await apiClient.get('/api/v1/admin/users');
      // setUsers(res.data);
      // Mock data
      setUsers([
        { id: 1, email: 'farmer1@example.com', full_name: 'John Doe', role: 'farmer', is_active: true, last_login: '2023-10-27T10:00:00Z' },
        { id: 2, email: 'scientist1@example.com', full_name: 'Jane Smith', role: 'scientist', is_active: true, last_login: '2023-10-26T15:30:00Z' },
        { id: 3, email: 'inactive@example.com', full_name: 'Bob Johnson', role: 'farmer', is_active: false, last_login: null },
      ]);
      setLoading(false);
    };

    if (user?.role === 'admin') {
      fetchUsers();
    }
  }, [user]);

  const filteredUsers = users.filter(u =>
    u.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    u.full_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const columns = [
    { header: t('user_table_id'), accessorKey: 'id' },
    { header: t('user_table_name'), accessorKey: 'full_name' },
    { header: t('user_table_email'), accessorKey: 'email' },
    {
      header: t('user_table_role'),
      accessorKey: 'role',
      cell: ({ row }: any) => <Badge variant={row.original.role === 'admin' ? 'default' : 'secondary'}>{row.original.role}</Badge>,
    },
    {
      header: t('user_table_status'),
      accessorKey: 'is_active',
      cell: ({ row }: any) => (
        <Badge variant={row.original.is_active ? 'success' : 'destructive'}>
          {row.original.is_active ? t('user_status_active') : t('user_status_inactive')}
        </Badge>
      ),
    },
    {
      header: t('actions'),
      cell: ({ row }: any) => (
        <div className="flex space-x-2">
          <Button size="sm" variant="ghost"><Eye className="h-4 w-4" /></Button>
          <Button size="sm" variant="ghost"><Edit className="h-4 w-4" /></Button>
          <Button size="sm" variant="ghost"><Trash2 className="h-4 w-4" /></Button>
        </div>
      ),
    },
  ];

  if (!user || user.role !== 'admin') {
    return (
      <div className="flex items-center justify-center h-[70vh]">
        <div className="text-center">
          <p className="text-lg text-red-500">{t('admin_access_denied')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
        <h1 className="text-3xl font-bold">{t('admin_users_title')}</h1>
        <Button><UserPlus className="mr-2 h-4 w-4" /> {t('admin_add_user')}</Button>
      </div>

      <div className="flex items-center py-4">
        <Input
          placeholder={t('user_search_placeholder')}
          value={searchTerm}
          onChange={(event) => setSearchTerm(event.target.value)}
          className="max-w-sm"
        />
        <Button variant="outline" size="icon" className="ml-2">
          <Search className="h-4 w-4" />
        </Button>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <p>{t('loading')}...</p>
        </div>
      ) : (
        <DataTable columns={columns} data={filteredUsers} />
      )}
    </div>
  );
}