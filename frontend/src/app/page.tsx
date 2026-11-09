'use client';

import { PageTransition } from '@/shared/ui/PageTransition';
import { useUnit } from 'effector-react';
import { $isAuth } from '@/shared/config/store';
import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';
import { HomeWidget } from '@/widgets/homeWidget/ui';
import { AuthorizedHome } from '@/widgets/authorizedHome/ui';

export default function Home() {
  const isAuth = useUnit($isAuth);

  return (
    <div className="home-palette relative z-10">
      <Header />
      <PageTransition>
        {isAuth ? <AuthorizedHome /> : <HomeWidget />}
      </PageTransition>
      <Footer />
    </div>
  );
}
