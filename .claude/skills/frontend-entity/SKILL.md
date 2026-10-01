---
name: frontend-entity
description: >
  Скаффолд слоя данных фронтенда BScout — models/<entity> из 4 файлов
  (schema.ts на Zod, service.ts на axios, hooks.ts на React Query, index.ts barrel).
  Используй, когда нужно подключить новую сущность бэкенда к фронтенду или
  добавить набор API-запросов/хуков (например "добавь модель отзывов на фронте",
  "хуки для избранного", "запросы к /api/brands").
argument-hint: "[entity-name]"
allowed-tools: Read, Grep, Glob, Write, Edit, Bash(npm run *), Bash(npx *)
---

# Скаффолд frontend-сущности: `$1`

Создай `src/models/$1/` строго по форме существующих слайсов
(эталон — `src/models/auth/` и `src/models/product/`). Сначала прочитай их.

## Файлы (ровно 4)

1. **`schema.ts`** — Zod-схемы запросов/ответов + выводимые типы (`z.infer`). Именование как в `models/auth/schema.ts`.
2. **`service.ts`** — объект `${1}Api` с методами, вызывающими `api` из `@/shared/api/axios` (пути `/api/$1/...`). Возвращать распарсенные данные/`AxiosResponse` как в эталоне.
3. **`hooks.ts`** — `use...`-хуки на `@tanstack/react-query` (`useQuery` для чтения, `useMutation` для записи), с `queryKey: ['$1', ...]` и `invalidateQueries` при мутациях.
4. **`index.ts`** — barrel: реэкспорт схем, типов, `${1}Api` и хуков.

## Конвенции (соблюдать)
- Серверное состояние — только React Query; не заводить Effector-стор без необходимости.
- Импорты через `@/*`.
- Типы выводить из Zod (`z.infer`), не дублировать вручную.
- Токены/заголовки не трогать — их ставит интерцептор в `shared/api/axios.ts`.

## После
`cd frontend && npm run build && npm run lint`. Не коммить без запроса. Покажи созданные файлы.
