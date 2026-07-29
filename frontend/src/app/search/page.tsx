'use client';

import { Suspense, useCallback, useState, useEffect } from 'react';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { useProductSearch } from '@/models/product';
import { useStores } from '@/models/store';
import { useCategories } from '@/models/category';
import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';
import { SearchBar, SearchFilters } from '@/features/search';
import { SearchResults } from '@/widgets/SearchResults/ui/SearchResults';

function SearchPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  // URL params — source of truth
  const q = searchParams.get('q') || '';
  const storeSlug = searchParams.get('store') || '';
  const categorySlug = searchParams.get('category') || '';
  const minPrice = searchParams.get('min_price') || '';
  const maxPrice = searchParams.get('max_price') || '';
  const inStockParam = searchParams.get('in_stock') || '';
  const sortBy = searchParams.get('sort_by') || 'price_asc';
  const page = parseInt(searchParams.get('page') || '1', 10);

  // Local input state (synced from URL)
  const [searchInput, setSearchInput] = useState(q);

  useEffect(() => { setSearchInput(q); }, [q]);

  // Data
  const { data, isLoading, isError } = useProductSearch({
    q,
    store: storeSlug || undefined,
    category: categorySlug || undefined,
    min_price: minPrice || undefined,
    max_price: maxPrice || undefined,
    in_stock: inStockParam === 'true' ? true : undefined,
    sort_by: sortBy,
    page,
    per_page: 20,
  });

  const { data: stores } = useStores();
  const { data: categories } = useCategories();

  const products = data?.results ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / (data?.per_page ?? 20));

  // Build URL from overrides
  const buildUrl = useCallback(
    (overrides: Record<string, string | undefined>) => {
      const params = new URLSearchParams();
      const merged = {
        q, store: storeSlug, category: categorySlug,
        min_price: minPrice, max_price: maxPrice,
        in_stock: inStockParam, sort_by: sortBy, page: String(page),
        ...overrides,
      };
      for (const [key, val] of Object.entries(merged)) {
        if (val) params.set(key, val);
      }
      return `${pathname}?${params.toString()}`;
    },
    [pathname, q, storeSlug, categorySlug, minPrice, maxPrice, inStockParam, sortBy, page],
  );

  const navigate = useCallback(
    (overrides: Record<string, string | undefined>) => {
      router.push(buildUrl(overrides));
    },
    [router, buildUrl],
  );

  // Handler creators
  const handleSearch = useCallback(() => {
    navigate({ q: searchInput, page: '1' });
  }, [navigate, searchInput]);

  const handleStoreToggle = useCallback(
    (slug: string) => navigate({ store: storeSlug === slug ? undefined : slug, page: '1' }),
    [navigate, storeSlug],
  );

  const handleCategoryToggle = useCallback(
    (slug: string) => navigate({ category: categorySlug === slug ? undefined : slug, page: '1' }),
    [navigate, categorySlug],
  );

  const handleInStockToggle = useCallback(
    () => navigate({ in_stock: inStockParam === 'true' ? undefined : 'true', page: '1' }),
    [navigate, inStockParam],
  );

  const handlePriceApply = useCallback(
    (min: string, max: string) => navigate({ min_price: min || undefined, max_price: max || undefined, page: '1' }),
    [navigate],
  );

  const handleSortChange = useCallback(
    (v: string) => navigate({ sort_by: v, page: '1' }),
    [navigate],
  );

  const handlePageChange = useCallback(
    (newPage: number) => {
      if (newPage < 1 || newPage > totalPages) return;
      navigate({ page: String(newPage) });
    },
    [navigate, totalPages],
  );

  const handleReset = useCallback(() => {
    setSearchInput('');
    router.push(pathname);
  }, [router, pathname]);

  return (
    <>
      <Header />
      <div className="max-w-[1200px] mx-auto px-6">
        <div className="grid grid-cols-[264px_1fr] gap-8 py-8 min-h-[calc(100vh-64px)] max-lg:grid-cols-1">
          {/* Filters sidebar */}
          <SearchFilters
            stores={stores}
            categories={categories}
            storeSlug={storeSlug}
            categorySlug={categorySlug}
            inStockParam={inStockParam}
            priceMin={minPrice}
            priceMax={maxPrice}
            onStoreToggle={handleStoreToggle}
            onCategoryToggle={handleCategoryToggle}
            onInStockToggle={handleInStockToggle}
            onPriceApply={handlePriceApply}
            onReset={handleReset}
          />

          {/* Main column */}
          <main>
            {/* Breadcrumbs */}
            <div className="flex items-center gap-2 text-[14px] text-body-muted mb-4 flex-wrap">
              <Link href="/" className="text-body-subtle no-underline hover:text-slate hover:underline">
                Главная
              </Link>
              <span className="text-body-muted">/</span>
              <span>Поиск</span>
            </div>

            {/* Search bar */}
            <SearchBar
              query={searchInput}
              onQueryChange={setSearchInput}
              onSubmit={handleSearch}
            />

            {/* Results */}
            <SearchResults
              products={products}
              total={total}
              totalPages={totalPages}
              page={page}
              sortBy={sortBy}
              isLoading={isLoading}
              isError={isError}
              onPageChange={handlePageChange}
              onSortChange={handleSortChange}
            />
          </main>
        </div>
      </div>
      <Footer />
    </>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={null}>
      <SearchPageContent />
    </Suspense>
  );
}
