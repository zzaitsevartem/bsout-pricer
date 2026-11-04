import axios from 'axios';
import type { CatalogSortOption } from '@/models/catalog';

export const PER_PAGE = 20;
export const OFFERS_PER_PAGE = 20;

export const SORT_OPTIONS: { value: CatalogSortOption; label: string }[] = [
  { value: 'min_price_asc', label: 'Сначала дешёвые' },
  { value: 'min_price_desc', label: 'Сначала дорогие' },
];

export type FilterKey =
  | 'device_id'
  | 'part_type_id'
  | 'quality_tier_id'
  | 'store'
  | 'min_price'
  | 'max_price'
  | 'in_stock';
export type FilterValue = string | number | boolean | null;
export type StoreOption = { slug: string; name: string };

export type FilterOption = { id: number; label: string };

export type CatalogFacets = {
  devices: FilterOption[];
  partTypes: FilterOption[];
  qualityTiers: FilterOption[];
  stores?: StoreOption[];
};

export const EMPTY_FACETS: CatalogFacets = { devices: [], partTypes: [], qualityTiers: [] };

export type SearchUrlState = {
  q: string;
  device_id?: number;
  part_type_id?: number;
  quality_tier_id?: number;
  store?: string;
  min_price?: number;
  max_price?: number;
  in_stock?: boolean;
  sort_by: CatalogSortOption;
  page: number;
};

export type SearchControls = {
  onQueryChange: (value: string) => void;
  onFilterChange: (key: FilterKey, value: FilterValue) => void;
  onPriceChange: (min: number | null, max: number | null) => void;
  onSortChange: (value: CatalogSortOption) => void;
  onPageChange: (value: number) => void;
  onReset: () => void;
};

export function parsePrice(raw: string | null): number | undefined {
  if (!raw?.trim()) return undefined;
  const value = Number(raw);
  return Number.isFinite(value) && value >= 0 ? value : undefined;
}

export function parseStock(raw: string | null): boolean | undefined {
  return raw === 'true' ? true : raw === 'false' ? false : undefined;
}

export function parseSort(raw: string | null): CatalogSortOption {
  return raw === 'min_price_desc' ? 'min_price_desc' : 'min_price_asc';
}

export function parseId(raw: string | null): number | undefined {
  if (!raw) {
    return undefined;
  }
  const value = Number(raw);
  if (!Number.isInteger(value) || value < 1) {
    return undefined;
  }
  return value;
}

export function parsePage(raw: string | null): number {
  const value = Number(raw);
  if (!Number.isInteger(value) || value < 1) {
    return 1;
  }
  return value;
}

export function pluralRu(count: number, one: string, few: string, many: string): string {
  const mod10 = Math.abs(count) % 10;
  const mod100 = Math.abs(count) % 100;
  if (mod10 === 1 && mod100 !== 11) {
    return one;
  }
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) {
    return few;
  }
  return many;
}

export function formatPrice(value: string | null): string {
  if (value === null) {
    return '—';
  }
  const amount = Number(value);
  if (!Number.isFinite(amount)) {
    return value;
  }
  return `${amount.toLocaleString('ru-RU', { maximumFractionDigits: 0 })} ₽`;
}

export function storesLabel(count: number): string {
  return `${count} ${pluralRu(count, 'магазин', 'магазина', 'магазинов')}`;
}

export function offersLabel(count: number): string {
  return `${count} ${pluralRu(count, 'предложение', 'предложения', 'предложений')}`;
}

export function foundLabel(total: number): string {
  return `Найдено: ${total} ${pluralRu(total, 'товар', 'товара', 'товаров')}`;
}

export function withSelected(
  options: FilterOption[],
  selectedId: number | undefined,
): FilterOption[] {
  if (selectedId === undefined || options.some((option) => option.id === selectedId)) {
    return options;
  }
  return [{ id: selectedId, label: `Выбрано #${selectedId}` }, ...options];
}

export function buildPageItems(page: number, totalPages: number): (number | 'gap')[] {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, index) => index + 1);
  }

  const numbers = new Set<number>([1, totalPages]);
  for (let value = page - 1; value <= page + 1; value += 1) {
    numbers.add(value);
  }
  if (page <= 4) {
    numbers.add(2);
    numbers.add(3);
    numbers.add(4);
  }
  if (page >= totalPages - 3) {
    numbers.add(totalPages - 1);
    numbers.add(totalPages - 2);
    numbers.add(totalPages - 3);
  }

  const sorted = Array.from(numbers)
    .filter((value) => value >= 1 && value <= totalPages)
    .sort((a, b) => a - b);

  const items: (number | 'gap')[] = [];
  sorted.forEach((value, index) => {
    if (index > 0 && value - sorted[index - 1] > 1) {
      items.push('gap');
    }
    items.push(value);
  });
  return items;
}

export function apiErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === 'string' && detail.length > 0) {
      return detail;
    }
  }
  return fallback;
}
