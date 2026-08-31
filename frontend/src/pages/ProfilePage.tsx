import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  User,
  Settings,
  Leaf,
  Droplets,
  Coins,
  TrendingUp,
  Award,
  Calendar,
  MapPin,
  Edit2,
  LogOut,
  Bell,
} from 'lucide-react';
import { AppLayout } from '../components/layout/AppLayout';
import { Card, Button, StatCard, ProgressRing } from '../components/ui';

export const ProfilePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');

  const userStats = [
    {
      title: 'کل کربن ذخیره‌شده',
      value: 45.8,
      suffix: ' تن CO₂',
      icon: <Leaf size={24} />,
      color: 'primary',
    },
    {
      title: 'آب ذخیره‌شده',
      value: 2850,
      suffix: ' m³',
      icon: <Droplets size={24} />,
      color: 'info',
    },
    {
      title: 'اعتبار کربن',
      value: 38,
      suffix: ' USDT',
      icon: <Coins size={24} />,
      color: 'accent',
    },
    {
      title: 'امتیاز پایداری',
      value: 87,
      suffix: '/۱۰۰',
      icon: <Award size={24} />,
      color: 'success',
    },
  ];

  const recentActivities = [
    {
      action: 'اجرای شبیه‌سازی کشت گندم',
      time: '۲ ساعت پیش',
      icon: <Leaf size={16} />,
      color: 'var(--color-success)',
    },
    {
      action: 'ثبت ۳.۲ تن CO₂ در بلاکچین',
      time: 'دیروز',
      icon: <Coins size={16} />,
      color: 'var(--color-accent)',
    },
    {
      action: 'طراحی بادشکن جدید',
      time: '۳ روز پیش',
      icon: <TrendingUp size={16} />,
      color: 'var(--color-info)',
    },
    {
      action: 'به‌روزرسانی مشخصات خاک',
      time: 'هفته پیش',
      icon: <Settings size={16} />,
      color: 'var(--color-warning)',
    },
  ];

  return (
    <AppLayout>
      <div style={{ maxWidth: 1400, margin: '0 auto', padding: '2rem' }}>
        {/* Profile Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            background: 'linear-gradient(135deg, var(--color-primary), var(--color-info))',
            borderRadius: 'var(--radius-2xl)',
            padding: '3rem 2rem',
            color: 'white',
            marginBottom: '2rem',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              position: 'absolute',
              top: -50,
              right: -50,
              width: 300,
              height: 300,
              borderRadius: '50%',
              background: 'rgba(255, 255, 255, 0.1)',
              filter: 'blur(60px)',
            }}
          />

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '2rem',
              position: 'relative',
              zIndex: 1,
            }}
          >
            <div
              style={{
                width: 100,
                height: 100,
                borderRadius: '50%',
                background: 'white',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--color-primary)',
                fontSize: '2.5rem',
                fontWeight: 700,
              }}
            >
              HA
            </div>
            <div style={{ flex: 1 }}>
              <h1 style={{ margin: 0, fontSize: '2rem', marginBottom: '0.5rem' }}>جناب آقای حسن</h1>
              <p style={{ margin: 0, opacity: 0.9, marginBottom: '1rem' }}>
                دانشمند و کارآفرین برجسته | کشاورزی پایدار
              </p>
              <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.875rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <MapPin size={16} />
                  <span>تهران، ایران</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Calendar size={16} />
                  <span>عضویت از ۱۴۰۵/۰۱/۰۱</span>
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <Button
                variant="secondary"
                style={{ background: 'rgba(255,255,255,0.2)', color: 'white', border: 'none' }}
              >
                <Edit2 size={16} />
                ویرایش
              </Button>
              <Button
                variant="secondary"
                style={{ background: 'rgba(255,255,255,0.2)', color: 'white', border: 'none' }}
              >
                <Bell size={16} />
              </Button>
            </div>
          </div>
        </motion.div>

        {/* Stats */}
        <div className="grid grid-cols-4" style={{ marginBottom: '2rem' }}>
          {userStats.map((stat, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <StatCard
                title={stat.title}
                value={stat.value}
                icon={stat.icon}
                color={stat.color as any}
              />
            </motion.div>
          ))}
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '2rem' }}>
          {[
            { id: 'overview', label: 'نمای کلی' },
            { id: 'farms', label: 'مزارع من' },
            { id: 'scenarios', label: 'سناریوها' },
            { id: 'credits', label: 'اعتبار کربن' },
            { id: 'settings', label: 'تنظیمات' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`btn ${activeTab === tab.id ? 'btn-primary' : 'btn-secondary'}`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab === 'overview' && (
          <div className="grid grid-cols-2">
            {/* Sustainability Score */}
            <Card title="امتیاز پایداری کلی" icon={<Award size={20} />}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '2rem',
                  padding: '2rem',
                }}
              >
                <ProgressRing
                  value={87}
                  size={150}
                  strokeWidth={12}
                  color="var(--color-success)"
                  label="عالی"
                />
                <div style={{ textAlign: 'right' }}>
                  <h3 style={{ marginBottom: '0.5rem' }}>وضعیت: عالی</h3>
                  <p
                    style={{
                      color: 'var(--color-text-secondary)',
                      lineHeight: 1.8,
                      marginBottom: '1rem',
                    }}
                  >
                    شما در بین ۱۰٪ بالای کاربران از نظر پایداری هستید!
                  </p>
                  <Button variant="primary" size="sm">
                    مشاهده گزارش کامل
                  </Button>
                </div>
              </div>
            </Card>

            {/* Recent Activity */}
            <Card title="فعالیت‌های اخیر" icon={<TrendingUp size={20} />}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {recentActivities.map((activity, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.75rem',
                      padding: '0.75rem',
                      background: 'var(--color-surface)',
                      borderRadius: 'var(--radius-lg)',
                    }}
                  >
                    <div
                      style={{
                        width: 32,
                        height: 32,
                        borderRadius: '50%',
                        background: `${activity.color}20`,
                        color: activity.color,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      {activity.icon}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '0.875rem', fontWeight: 500 }}>{activity.action}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>
                        {activity.time}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </Card>
          </div>
        )}

        {activeTab === 'farms' && (
          <Card title="مزارع من" icon={<MapPin size={20} />}>
            <div
              style={{ padding: '3rem', textAlign: 'center', color: 'var(--color-text-tertiary)' }}
            >
              <MapPin size={64} style={{ margin: '0 auto 1rem', opacity: 0.3 }} />
              <h3>هنوز مزرعه‌ای ثبت نکرده‌اید</h3>
              <p style={{ marginBottom: '1.5rem' }}>
                اولین مزرعه خود را ثبت کنید تا شبیه‌سازی را شروع کنید
              </p>
              <Button variant="primary">ثبت مزرعه جدید</Button>
            </div>
          </Card>
        )}

        {activeTab === 'settings' && (
          <Card title="تنظیمات حساب" icon={<Settings size={20} />}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <Button variant="secondary" style={{ justifyContent: 'flex-start' }}>
                <User size={16} /> اطلاعات شخصی
              </Button>
              <Button variant="secondary" style={{ justifyContent: 'flex-start' }}>
                <Bell size={16} /> تنظیمات اعلان‌ها
              </Button>
              <Button variant="secondary" style={{ justifyContent: 'flex-start' }}>
                <Settings size={16} /> امنیت حساب
              </Button>
              <Button
                variant="secondary"
                style={{ justifyContent: 'flex-start', color: 'var(--color-error)' }}
              >
                <LogOut size={16} /> خروج از حساب
              </Button>
            </div>
          </Card>
        )}
      </div>
    </AppLayout>
  );
};
