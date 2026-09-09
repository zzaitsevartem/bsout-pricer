'use client';

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { useUnit } from 'effector-react';
import { $authReady, $isAuth } from '@/shared/config/store';
import type { CatalogSortOption } from '@/models/catalog';
import { SearchLayout } from '@/app/search/_components/SearchLayout';
import { CatalogSearchView } from '@/app/search/_components/CatalogSearchView';
import { ResultsSkeleton } from '@/app/search/_components/ResultsSkeleton';
import { EMPTY_FACETS, parseId, parsePage, parseSort } from '@/app/search/_components/lib';
import type { FilterKey, SearchControls, SearchUrlState } from '@/app/search/_components/lib';

const DEBOUNCE_MS = 350;

export function SearchClient() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const isAuth = useUnit($isAuth);
  const authReady = useUnit($authReady);

  const q = searchParams.get('q') ?? '';

  const state = useMemo<SearchUrlState>(
    () => ({
      q,
      device_id: parseId(searchParams.get('device_id')),
      part_type_id: parseId(searchParams.get('part_type_id')),
      quality_tier_id: parseId(searchParams.get('quality_tier_id')),
      sort_by: parseSort(searchParams.get('sort_by')),
      page: parsePage(searchParams.get('page')),
    }),
    [q, searchParams],
  );

  const commit = useCallback(
    (patch: Record<string, string | number | null>) => {
      const next = new URLSearchParams(searchParams.toString());
      Object.entries(patch).forEach(([key, value]) => {
        if (value === null || value === '') {
          next.delete(key);
        } else {
          next.set(key, String(value));
        }
      });
      const queryString = next.toString();
      router.replace(queryString ? `${pathname}?${queryString}` : pathname, { scroll: false });
    },
    [pathname, router, searchParams],
  );

  const [text, setText] = useState(q);
  const committedRef = useRef(q);

  useEffect(() => {
    if (q !== committedRef.current) {
      committedRef.current = q;
      setText(q);
    }
  }, [q]);

  useEffect(() => {
    if (text === committedRef.current) {
      return;
    }
    const timer = setTimeout(() => {
      committedRef.current = text;
      commit({ q: text || null, page: null });
    }, DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [text, commit]);

  const onSubmit = useCallback(() => {
    committedRef.current = text;
    commit({ q: text || null, page: null });
  }, [commit, text]);

  const onFilterChange = useCallback(
    (key: FilterKey, value: number | null) => {
      commit({ [key]: value, page: null });
    },
    [commit],
  );

  const onSortChange = useCallback(
    (value: CatalogSortOption) => {
      commit({ sort_by: value === 'min_price_asc' ? null : value, page: null });
    },
    [commit],
  );

  const onPageChange = useCallback(
    (value: number) => {
      commit({ page: value <= 1 ? null : value });
      if (typeof window !== 'undefined') {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    },
    [commit],
  );

  const onReset = useCallback(() => {
    commit({ device_id: null, part_type_id: null, quality_tier_id: null, page: null });
  }, [commit]);

  const controls = useMemo<SearchControls>(
    () => ({
      text,
      onTextChange: setText,
      onSubmit,
      onFilterChange,
      onSortChange,
      onPageChange,
      onReset,
    }),
    [text, onSubmit, onFilterChange, onSortChange, onPageChange, onReset],
  );

  if (!authReady) {
    return (
      <SearchLayout state={state} controls={controls} facets={EMPTY_FACETS} summary="Загрузка…">
        <ResultsSkeleton />
      </SearchLayout>
    );
  }

  if (!isAuth) {
    return (
      <SearchLayout
        state={state}
        controls={controls}
        facets={EMPTY_FACETS}
        summary="Поиск доступен после входа"
      >
        <div className="rounded-[24px] bg-ivory-elevated p-8 text-center">
          <p className="text-base font-semibold text-slate mb-2">Войдите, чтобы искать по каталогу</p>
          <p className="text-[15px] text-body-subtle mb-6">
            Сравнение цен между магазинами доступно авторизованным пользователям.
          </p>
          <div className="flex items-center justify-center gap-3 flex-wrap">
            <Link href="/login" className="btn-primary">
              Войти
            </Link>
            <Link href="/register" className="btn-secondary">
              Регистрация
            </Link>
          </div>
        </div>
      </SearchLayout>
    );
  }

  return <CatalogSearchView state={state} controls={controls} />;
}
