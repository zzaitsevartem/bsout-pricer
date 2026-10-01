---
name: design-system
description: >
  Дизайн-система BScout для любой UI-работы: вёрстка страниц, компоненты,
  кнопки, карточки, формы, типографика, цвета, отступы, тени, состояния.
  Используй ПЕРЕД написанием любого JSX/вёрстки или стилей. Модули лежат
  в bsout-pricer/skills/claude/ (импортированная система TypeUI).
allowed-tools: Read, Grep, Glob
---

# Дизайн-система BScout

Полная система описана в `bsout-pricer/skills/claude/` — это каталог **внутреннего** репозитория
`bsout-pricer/`, а не внешнего `bscount/`. Если ты запущен из внешней папки, путь к модулям —
`bsout-pricer/skills/claude/`. Это спецификация *как выглядит* дизайн — реализацию
(Tailwind-классы / CSS-переменные) выбираешь сам.

## Обязательный порядок
1. **Прочитать `bsout-pricer/skills/claude/SKILL.md`** — общий стиль, критические правила, список модулей.
2. **Прочитать релевантные модули ПЕРЕД кодом.** Для лендинга минимум: `layout.md`, `typography.md`, `colors.md`, `buttons.md`, `cards.md`, `shadows.md`, `radius.md`, `borders.md`. Для форм — добавь `inputs.md`, `radios-checkboxes-toggle.md`. Для навигации — `sidebars.md`, `dropdown.md`, `tabs.md`.
3. **Кросс-проверка**: карточка с кнопкой обязана удовлетворять и `cards.md`, и `buttons.md`.

## Ключевые правила системы
- Токены в `.md` — **абстрактные, не имена классов**: маппишь их на CSS-переменные / Tailwind-конфиг сам.
- Тёмная тема — цвета вручную не свапать, только через токены. **Внимание:** модули TypeUI описывают
  переключение через `prefers-color-scheme`, но в проекте это `darkMode: 'class'` — переменные
  переопределяются в `.dark` (`frontend/src/app/globals.css`). Здесь приоритет у проекта.
- У каждого интерактивного элемента — hover / focus / disabled.
- Семантический HTML, корректная иерархия заголовков, ARIA где нужно.

## Связь с проектными токенами
Палитра проекта **совпадает** с системой TypeUI (ivory/slate/clay) — она из неё и выведена.
Реализация: CSS-переменные в `frontend/src/app/globals.css` (`:root` + `.dark`), имена
Tailwind — в `frontend/tailwind.config.ts`.

| Группа | Tailwind-имена | Light |
|---|---|---|
| Поверхности | `ivory`, `ivory-elevated`, `ivory-warm` | `#FAF9F5`, `#F0EEE6`, `#E3DACC` |
| Тёмные / текст | `slate`, `slate-soft`, `slate-medium` | `#141413`, `#1F1F1D`, `#282825` |
| Текст | `body`, `body-subtle`, `body-muted` | `#3D3D3A`, `#5E5D59`, `#87867F` |
| Границы | `border-default`, `border-light`, `border-subtle`, `border-light-subtle` | `#B0AEA5`, `#E3DACC`, `#D1CFC5`, `#E8E6DC` |
| Акценты (фикс. hex, без переменных) | `clay`, `clay-ember`, `olive`, `sky`, `fig`, `cactus`, `green-discount` | `#D97757`, `#C6613F`, `#788C5D`, `#6A9BCC`, `#C46686`, `#BCD1CA`, `#22c55e` |

Шрифты: `font-raleway` (основной), `font-dm-sans`, `font-lexend`, `font-montserrat`.
Готовые классы кнопок (`.btn-primary/secondary/ghost/danger/sm/lg/icon/arrow`) уже описаны
в `globals.css` — используй их, а не собирай кнопку заново.

При конфликте с TypeUI-модулями — приоритет у `frontend/tailwind.config.ts`,
`frontend/src/app/globals.css` и `.claude/rules/frontend.md`.

Полный список доступных модулей:
!`d=""; for c in "${CLAUDE_PROJECT_DIR:-}" "$PWD" "$PWD/.." "$PWD/../.."; do for s in "$c/bsout-pricer/skills/claude" "$c/skills/claude"; do [ -d "$s" ] && d="$s" && break 2; done; done; [ -n "$d" ] && ls "$d" || echo "модули дизайн-системы не найдены"`
