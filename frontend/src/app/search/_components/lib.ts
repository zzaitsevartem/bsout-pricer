import axios from 'axios';
import type { CatalogItemResponse, CatalogSortOption } from '@/models/catalog';

export const PER_PAGE = 20;
export const FACETS_SAMPLE_SIZE = 100;

export const SORT_OPTIONS: { value: CatalogSortOption; label: string }[] = [
  { value: 'min_price_asc', label: 'Сначала дешёвые' },
  { value: 'min_price_desc', label: 'Сначала дорогие' },
];

export type FilterKey = 'device_id' | 'part_type_id' | 'quality_tier_id';

export type FilterOption = { id: number; label: string };

export type CatalogFacets = {
  devices: FilterOption[];
  partTypes: FilterOption[];
  qualityTiers: FilterOption[];
};

export const EMPTY_FACETS: CatalogFacets = { devices: [], partTypes: [], qualityTiers: [] };

export type SearchUrlState = {
  q: string;
  device_id?: number;
  part_type_id?: number;
  quality_tier_id?: number;
  sort_by: CatalogSortOption;
  page: number;
};

export type SearchControls = {
  text: string;
  onTextChange: (value: string) => void;
  onSubmit: () => void;
  onFilterChange: (key: FilterKey, value: number | null) => void;
  onSortChange: (value: CatalogSortOption) => void;
  onPageChange: (value: number) => void;
  onReset: () => void;
};

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

export function collectFacets(items: CatalogItemResponse[]): CatalogFacets {
  const devices = new Map<number, string>();
  const partTypes = new Map<number, string>();
  const qualityTiers = new Map<number, { label: string; rank: number }>();

  for (const item of items) {
    if (item.device) {
      devices.set(item.device.id, item.device.name);
    }
    if (item.part_type) {
      partTypes.set(item.part_type.id, item.part_type.name_ru);
    }
    if (item.quality_tier) {
      qualityTiers.set(item.quality_tier.id, {
        label: item.quality_tier.name_ru,
        rank: item.quality_tier.rank,
      });
    }
  }

  const byLabel = (a: FilterOption, b: FilterOption) => a.label.localeCompare(b.label, 'ru');

  return {
    devices: Array.from(devices, ([id, label]) => ({ id, label })).sort(byLabel),
    partTypes: Array.from(partTypes, ([id, label]) => ({ id, label })).sort(byLabel),
    qualityTiers: Array.from(qualityTiers, ([id, value]) => ({ id, ...value }))
      .sort((a, b) => a.rank - b.rank)
      .map(({ id, label }) => ({ id, label })),
  };
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
