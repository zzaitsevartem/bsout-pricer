'use client';

import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';
import { ProductDetail } from '@/widgets/ProductDetail/ui/ProductDetail';

function ProductPageContent() {
  const searchParams = useSearchParams();
  const id = searchParams.get('id');

  return (
    <>
      <Header />
      <ProductDetail productId={id ? Number(id) : null} />
      <Footer />
    </>
  );
}

export default function ProductPage() {
  return (
    <Suspense>
      <ProductPageContent />
    </Suspense>
  );
}
