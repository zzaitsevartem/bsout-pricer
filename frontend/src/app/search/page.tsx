import { PageTransition } from '@/shared/ui/PageTransition';
import React, { Suspense } from 'react';
import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';
import { SearchClient } from '@/app/search/_components/SearchClient';
import { SearchFallback } from '@/app/search/_components/SearchFallback';

export default function SearchPage() {
  return (
    <>
      <Header />
      <PageTransition>
        <Suspense fallback={<SearchFallback />}>
          <SearchClient />
        </Suspense>
      </PageTransition>
      <Footer />
    </>
  );
}
