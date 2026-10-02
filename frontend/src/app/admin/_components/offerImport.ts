import { offerImportItemSchema, type OfferImportItem } from '@/models/admin';

export type OfferImportParseIssue = {
  index: number;
  reason: string;
};

export type OfferImportParseResult =
  | { ok: true; rows: OfferImportItem[]; issues: OfferImportParseIssue[]; total: number }
  | { ok: false; error: string };

export const MAX_IMPORT_ROWS = 5000;

function formatSchemaError(error: { issues: { path: (string | number)[]; message: string }[] }): string {
  return error.issues
    .map((issue) => {
      const field = issue.path.length > 0 ? issue.path.join('.') : 'строка';
      return `${field}: ${issue.message}`;
    })
    .join('; ');
}

export function parseOfferImportPayload(text: string): OfferImportParseResult {
  const trimmed = text.trim();

  if (trimmed === '') {
    return { ok: false, error: 'Вставьте JSON-массив офферов или загрузите файл.' };
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(trimmed);
  } catch {
    return { ok: false, error: 'Не удалось разобрать JSON — проверьте запятые и кавычки.' };
  }

  const list = Array.isArray(parsed) ? parsed : [parsed];

  if (list.length === 0) {
    return { ok: false, error: 'Массив пуст — импортировать нечего.' };
  }

  if (list.length > MAX_IMPORT_ROWS) {
    return {
      ok: false,
      error: `В файле ${list.length} строк, а за один раз принимается до ${MAX_IMPORT_ROWS}. Разбейте файл на части.`,
    };
  }

  const rows: OfferImportItem[] = [];
  const issues: OfferImportParseIssue[] = [];

  list.forEach((item, index) => {
    const result = offerImportItemSchema.safeParse(item);
    if (result.success) {
      rows.push(result.data);
    } else {
      issues.push({ index, reason: formatSchemaError(result.error) });
    }
  });

  return { ok: true, rows, issues, total: list.length };
}
