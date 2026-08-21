'use client';
import { useTheme } from '../../lib/theme-context';
import { motion } from 'framer-motion';
import { Moon, Sun } from 'lucide-react';

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <motion.button
      onClick={toggleTheme}
      whileHover={{ scale: 1.1, rotate: 15 }}
      whileTap={{ scale: 0.9 }}
      style={{
        width: '40px',
        height: '40px',
        borderRadius: '12px',
        border: 'none',
        background: theme === 'dark'
          ? 'linear-gradient(135deg, #1e293b, #334155)'
          : 'linear-gradient(135deg, #fef3c7, #fbbf24)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
        transition: 'all 0.3s ease',
      }}
      aria-label="Toggle theme"
    >
      {theme === 'dark' ? <Moon size={20} color="#fbbf24" /> : <Sun size={20} color="#f59e0b" />}
    </motion.button>
  );
}
