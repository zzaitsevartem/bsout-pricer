---
name: design-system
description: >
  Дизайн-система BScout для любой UI-работы: вёрстка страниц, компоненты,
  кнопки, карточки, формы, типографика, цвета, отступы, тени, состояния.
  Используй ПЕРЕД написанием любого JSX/вёрстки или стилей. Модули лежат
  в skills/claude/ (импортированная система TypeUI).
allowed-tools: Read, Grep, Glob
---

# Дизайн-система BScout

Полная система описана в `skills/claude/` (корень проекта). Это спецификация
*как выглядит* дизайн — реализацию (Tailwind-классы / CSS-переменные) выбираешь сам.

## Обязательный порядок
1. **Прочитать `skills/claude/SKILL.md`** — общий стиль, критические правила, список модулей.
2. **Прочитать релевантные модули ПЕРЕД кодом.** Для лендинга минимум: `layout.md`, `typography.md`, `colors.md`, `buttons.md`, `cards.md`, `shadows.md`, `radius.md`, `borders.md`. Для форм — добавь `inputs.md`, `radios-checkboxes-toggle.md`. Для навигации — `sidebars.md`, `dropdown.md`, `tabs.md`.
3. **Кросс-проверка**: карточка с кнопкой обязана удовлетворять и `cards.md`, и `buttons.md`.

## Ключевые правила системы
- Токены в `.md` — **абстрактные, не имена классов**: маппишь их на CSS-переменные / Tailwind-конфиг сам.
- Тёмная тема — автоматически через `prefers-color-scheme`, цвета вручную не свапать.
- У каждого интерактивного элемента — hover / focus / disabled.
- Семантический HTML, корректная иерархия заголовков, ARIA где нужно.

## Связь с проектными токенами
Проектные бренд-токены (в `frontend/tailwind.config.ts`): brand-dark `#010D3E`,
muted `#6F6C90`, accent `#b8007b`, шрифт Raleway. При конфликте с TypeUI-модулями —
приоритет у `frontend/tailwind.config.ts` и `.claude/rules/frontend.md`.

Полный список доступных модулей:
!`ls "${CLAUDE_PROJECT_DIR}/skills/claude" 2>/dev/null || ls skills/claude`
