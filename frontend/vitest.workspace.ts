import { defineWorkspace } from 'vitest/config';

export default defineWorkspace([
  {
    extends: './vitest.config.ts',
    test: {
      name: 'unit',
      environment: 'node',
      include: ['src/**/*.unit.test.ts'],
    },
  },
  {
    extends: './vitest.config.ts',
    test: {
      name: 'component',
      environment: 'jsdom',
      include: ['src/**/*.test.tsx'],
      setupFiles: ['./vitest.setup.ts'],
    },
  },
]);
