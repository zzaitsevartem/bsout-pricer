import { describe, expect, it } from 'vitest';

import { MAX_IMPORT_ROWS, parseOfferImportPayload } from './offerImport';

const validRow = {
  store_slug: 'profi',
  source_sku: '12345',
  title: 'Дисплей iPhone 13',
  price_retail: '3490',
};

function row(overrides: Record<string, unknown> = {}) {
  return JSON.stringify([{ ...validRow, ...overrides }]);
}

describe('parseOfferImportPayload', () => {
  it('rejects empty input', () => {
    const result = parseOfferImportPayload('   ');

    expect(result.ok).toBe(false);
  });

  it('rejects malformed JSON', () => {
    const result = parseOfferImportPayload('[{"store_slug": "profi",]');

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error).toContain('JSON');
    }
  });

  it('rejects an empty array', () => {
    const result = parseOfferImportPayload('[]');

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error).toContain('пуст');
    }
  });

  it('rejects a payload above the row limit', () => {
    const many = JSON.stringify(
      Array.from({ length: MAX_IMPORT_ROWS + 1 }, () => validRow),
    );
    const result = parseOfferImportPayload(many);

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error).toContain(String(MAX_IMPORT_ROWS));
    }
  });

  it('accepts a valid array and keeps every row', () => {
    const result = parseOfferImportPayload(row());

    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.total).toBe(1);
      expect(result.rows).toEqual([validRow]);
      expect(result.issues).toEqual([]);
    }
  });

  it('wraps a single object into a one-row batch', () => {
    const result = parseOfferImportPayload(JSON.stringify(validRow));

    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.rows).toHaveLength(1);
      expect(result.total).toBe(1);
    }
  });

  it('keeps numeric prices as sent', () => {
    const result = parseOfferImportPayload(row({ price_retail: 3490 }));

    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.rows[0]?.price_retail).toBe(3490);
    }
  });

  it('reports invalid rows by index and keeps the valid ones', () => {
    const payload = JSON.stringify([
      validRow,
      { ...validRow, source_sku: '' },
      { ...validRow, title: 'Корпус', store_slug: 'liberti' },
    ]);
    const result = parseOfferImportPayload(payload);

    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.total).toBe(3);
      expect(result.rows).toHaveLength(2);
      expect(result.issues).toHaveLength(1);
      expect(result.issues[0]?.index).toBe(1);
      expect(result.issues[0]?.reason).toContain('source_sku');
    }
  });

  it('returns no importable rows when every row is invalid', () => {
    const payload = JSON.stringify([{ store_slug: 'profi' }, { store_slug: 'profi' }]);
    const result = parseOfferImportPayload(payload);

    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.rows).toHaveLength(0);
      expect(result.issues).toHaveLength(2);
    }
  });

  it('rejects rows that are not objects', () => {
    const result = parseOfferImportPayload(JSON.stringify(['just a string']));

    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.rows).toHaveLength(0);
      expect(result.issues).toHaveLength(1);
    }
  });
});
