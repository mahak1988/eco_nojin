import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Leaf,
  Droplets,
  Wind,
  Sprout,
  Beef,
  LineChart,
  Map,
  Settings,
  X } from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const menuItems = [
  { id: 'dashboard', label: 'داشبورد', icon: LayoutDashboard, path: '/hydroma' },
  { id: 'crops', label: 'برنامه کشت', icon: Sprout, path: '/models' },
  { id: 'water', label: 'مدیریت آب', icon: Droplets, path: '/models/watershed' },
  { id: 'erosion', label: 'فرسایش', icon: Wind, path: '/terrain' },
  { id: 'livestock', label: 'دامداری', icon: Beef, path: '/simulator' },
  { id: 'carbon', label: 'کربن', icon: Leaf, path: '/models/rothc' },
  { id: 'maps', label: 'نقشه‌ها', icon: Map, path: '/virtual-lab' },
  { id: 'reports', label: 'گزارش‌ها', icon: LineChart, path: '/reports' },
  { id: 'settings', label: 'تنظیمات', icon: Settings, path: '/settings' },
];

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const [activeItem, setActiveItem] = useState('dashboard');
  const navigate = useNavigate();

  return (
    <>
      {/* Mobile Overlay */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0, 0, 0, 0.5)',
              zIndex: 40,
              display: 'none' }}
            className="md:hidden"
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{ x: isOpen ? 0 : -280 }}
        transition={{ type: 'spring', damping: 20 }}
        style={{
          width: 280,
          background: 'var(--color-surface)',
          borderRight: '1px solid var(--color-border)',
          display: 'flex',
          flexDirection: 'column',
          position: 'fixed',
          top: 0,
          left: 0,
          bottom: 0,
          zIndex: 50 }}
      >
        {/* Logo */}
        <div
          style={{
            padding: '1.5rem',
            borderBottom: '1px solid var(--color-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: 'var(--radius-xl)',
                background: 'linear-gradient(135deg, var(--color-primary), var(--color-accent))',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontWeight: 700,
                fontSize: '1.25rem' }}
            >
              🌱
            </div>
            <div>
              <h1 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0 }}>
                Eco Nojin
              </h1>
              <p style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)', margin: 0 }}>
                پلتفرم کشاورزی پایدار
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="btn btn-ghost md:hidden"
            style={{ padding: '0.5rem' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Menu */}
        <nav style={{ flex: 1, padding: '1rem', overflowY: 'auto' }}>
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeItem === item.id;

            return (
              <motion.button
                key={item.id}
                onClick={() => {
                  setActiveItem(item.id);
                  onClose();
                  navigate(item.path);
                }}
                whileHover={{ x: 4 }}
                whileTap={{ scale: 0.98 }}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '0.75rem 1rem',
                  borderRadius: 'var(--radius-lg)',
                  border: 'none',
                  background: isActive ? 'var(--color-primary)' : 'transparent',
                  color: isActive ? 'white' : 'var(--color-text-secondary)',
                  cursor: 'pointer',
                  marginBottom: '0.5rem',
                  transition: 'all 0.2s',
                  fontSize: '0.875rem',
                  fontWeight: isActive ? 600 : 400 }}
              >
                <Icon size={20} />
                <span>{item.label}</span>
              </motion.button>
            );
          })}
        </nav>

        {/* Footer */}
        <div
          style={{
            padding: '1rem',
            borderTop: '1px solid var(--color-border)',
            fontSize: '0.75rem',
            color: 'var(--color-text-tertiary)',
            textAlign: 'center' }}
        >
          <p style={{ margin: 0 }}>نسخه 4.0.0</p>
          <p style={{ margin: '0.25rem 0 0 0' }}>© 2026 Eco Nojin</p>
        </div>
      </motion.aside>
    </>
  );
};
