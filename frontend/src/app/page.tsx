'use client';

import { useUnit } from 'effector-react';
import { $isAuth } from '@/shared/config/store';
import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';
import { HomeWidget } from '@/widgets/homeWidget/ui';
import { AuthorizedHome } from '@/widgets/authorizedHome/ui';

export default function Home() {
  const isAuth = useUnit($isAuth);

  return (
    <div className="relative z-10">
      <Header />
      {isAuth ? <AuthorizedHome /> : <HomeWidget />}
      <Footer />
    </div>
  );
}
