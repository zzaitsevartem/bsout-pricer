'use client';

import React from 'react';
import { useTheme } from '@/shared/providers/ThemeProvider';
import { MoonIcon, SunIcon } from '@/shared/ui/IconSVG';

const ThemeToggle: React.FC = () => {
  const { toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className="flex items-center justify-center w-9 h-9 shrink-0 bg-transparent text-slate border border-border-subtle rounded-full cursor-pointer transition-colors hover:bg-ivory-elevated"
      aria-label="Переключить тему"
      title="Переключить тему"
    >
      <SunIcon className="block dark:hidden" />
      <MoonIcon className="hidden dark:block" />
    </button>
  );
};

export { ThemeToggle };
