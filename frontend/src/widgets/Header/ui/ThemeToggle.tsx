'use client';

import React from 'react';
import { useTheme } from '@/shared/providers/ThemeProvider';
import { MoonIcon, SunIcon } from '@/shared/ui/IconSVG';

const ThemeToggle: React.FC = () => {
  const { toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className="btn-icon"
      aria-label="Переключить тему"
      title="Переключить тему"
    >
      <SunIcon width={20} height={20} className="block dark:hidden" />
      <MoonIcon width={20} height={20} className="hidden dark:block" />
    </button>
  );
};

export { ThemeToggle };
