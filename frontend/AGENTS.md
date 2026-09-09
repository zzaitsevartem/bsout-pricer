# Frontend Rules

## Architecture

The frontend uses Next.js 14 App Router, React 18, TypeScript, Tailwind,
React Query, Effector, Axios, Zod, and Vitest.

- `src/app/`: routes, layouts, and global styles.
- `src/models/<entity>/`: data slices with exactly `schema.ts`, `service.ts`,
  `hooks.ts`, and `index.ts`.
- `src/widgets/`: composed page sections.
- `src/shared/`: API client, providers, client stores, utilities, UI, and assets.

Read `../DESIGN.md`, `../.claude/rules/frontend.md`, and the
`bscout-design-system` skill before UI or styling work.

## Conventions

- Use React Query for server state; reserve Effector for client authentication
  state.
- Match backend JSON in `snake_case`; infer TypeScript types from Zod schemas.
- Use `"use client"` only for React hooks or browser-only APIs.
- Import through `@/*`, not long relative paths.
- Use Tailwind utilities and tokens from `tailwind.config.ts`; do not add CSS
  modules or hardcode colors, fonts, animations, or shadows.
- Use `cn()` from `@/shared/lib/utils` for conditional classes.
- Import images from `@/shared/assets/images/` and use the established Next.js
  image pattern.
- Preserve semantic HTML, keyboard operation, accessible names, and visible
  focus states.

## Commands and Tests

```bash
npm install
npm run dev
npm run format:check
npm run build
npm run lint
npm test
npm run test:unit
npm run test:component
npm run test:coverage
```

Vitest uses Testing Library, jsdom, and MSW. Test observable behavior and add
regression tests for fixes. Run build, lint, and the relevant Vitest project
after changes.
