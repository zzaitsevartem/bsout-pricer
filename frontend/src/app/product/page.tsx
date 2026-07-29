'use client';

import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';
import { ProductDetail } from '@/widgets/ProductDetail/ui/ProductDetail';

export default function ProductPage() {
  return (
    <>
      <Header />
      <ProductDetail />
      <Footer />
    </>
  );
}
