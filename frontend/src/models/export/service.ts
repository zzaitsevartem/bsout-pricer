import axios from 'axios';
import { api } from '@/shared/api/axios';
import { exportErrorBodySchema } from './schema';
import type { ExportCatalogParams, ExportError, ExportedFile } from './schema';

const CATALOG_CSV_FILENAME = 'bscout-catalog.csv';
const TRACKING_CSV_FILENAME = 'bscout-tracking.csv';
const REVOKE_DELAY_MS = 10000;

const STATUS_FALLBACK: Record<number, string> = {
  401: 'Войдите в аккаунт, чтобы выгрузить отчёт.',
  403: 'Экспорт отчётов доступен не на всех тарифах.',
  404: 'Выгрузка недоступна.',
  429: 'Слишком много запросов. Попробуйте чуть позже.',
  503: 'Выгрузка в этом формате пока недоступна.',
};

const DEFAULT_FALLBACK = 'Не удалось выгрузить отчёт. Попробуйте ещё раз.';
const NETWORK_FALLBACK = 'Нет связи с сервером. Проверьте подключение и повторите.';

function createExportError(status: number, code: string, message: string): ExportError {
  return Object.assign(new Error(message), { status, code });
}

export function isExportError(value: unknown): value is ExportError {
  return (
    value instanceof Error &&
    typeof (value as ExportError).code === 'string' &&
    typeof (value as ExportError).status === 'number'
  );
}

async function readPayload(data: unknown): Promise<unknown> {
  if (typeof Blob !== 'undefined' && data instanceof Blob) {
    const text = await data.text();
    if (!text) {
      return null;
    }
    try {
      return JSON.parse(text);
    } catch {
      return text;
    }
  }
  return data;
}

async function toExportError(error: unknown): Promise<ExportError> {
  if (!axios.isAxiosError(error) || !error.response) {
    return createExportError(0, 'network_error', NETWORK_FALLBACK);
  }

  const status = error.response.status;
  const fallback = STATUS_FALLBACK[status] ?? DEFAULT_FALLBACK;

  let payload: unknown = null;
  try {
    payload = await readPayload(error.response.data);
  } catch {
    return createExportError(status, 'error', fallback);
  }

  const parsed = exportErrorBodySchema.safeParse(payload);
  if (!parsed.success) {
    return createExportError(status, 'error', fallback);
  }

  const detail = parsed.data.detail;
  if (typeof detail === 'string') {
    return createExportError(status, 'error', detail || fallback);
  }
  return createExportError(status, detail.code, detail.message || fallback);
}

function decodeFilename(raw: string): string {
  try {
    return decodeURIComponent(raw.trim());
  } catch {
    return raw.trim();
  }
}

function sanitizeFilename(raw: string, fallback: string): string {
  const cleaned = raw.replace(/[\\/]/g, '_').replace(/^\.+/, '').trim();
  return cleaned || fallback;
}

export function filenameFromDisposition(header: unknown, fallback: string): string {
  if (typeof header !== 'string' || !header) {
    return fallback;
  }

  const encoded = /filename\*=\s*(?:UTF-8|utf-8)''([^;]+)/.exec(header);
  if (encoded) {
    return sanitizeFilename(decodeFilename(encoded[1]), fallback);
  }

  const quoted = /filename\s*=\s*"([^"]*)"/i.exec(header);
  if (quoted) {
    return sanitizeFilename(quoted[1], fallback);
  }

  const bare = /filename\s*=\s*([^;]+)/i.exec(header);
  if (bare) {
    return sanitizeFilename(bare[1], fallback);
  }

  return fallback;
}

export function saveExportedFile(file: ExportedFile): void {
  if (typeof window === 'undefined' || typeof document === 'undefined') {
    return;
  }

  const url = window.URL.createObjectURL(file.blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = file.filename;
  link.rel = 'noopener';
  link.style.display = 'none';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.setTimeout(() => window.URL.revokeObjectURL(url), REVOKE_DELAY_MS);
}

async function downloadFile(
  path: string,
  fallbackName: string,
  params?: ExportCatalogParams,
): Promise<ExportedFile> {
  try {
    const response = await api.get<Blob>(path, { params, responseType: 'blob' });
    return {
      blob: response.data,
      filename: filenameFromDisposition(response.headers['content-disposition'], fallbackName),
    };
  } catch (error) {
    throw await toExportError(error);
  }
}

export const exportApi = {
  catalogCsv: (params: ExportCatalogParams) =>
    downloadFile('/export/catalog.csv', CATALOG_CSV_FILENAME, params),

  trackingCsv: () => downloadFile('/export/tracking.csv', TRACKING_CSV_FILENAME),
};
