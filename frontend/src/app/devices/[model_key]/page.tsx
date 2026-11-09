import { PageTransition } from '@/shared/ui/PageTransition';
import { Suspense } from 'react';
import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';
import { DeviceClient } from './DeviceClient';
export default function DevicePage({ params }: { params: { model_key: string } }) {
  return (
    <>
      <Header />
      <PageTransition>
        <Suspense
          fallback={
            <p role="status" className="p-8 text-body-subtle">
              Загрузка устройства…
            </p>
          }
        >
          <DeviceClient key={params.model_key} modelKey={params.model_key} />
        </Suspense>
      </PageTransition>
      <Footer />
    </>
  );
}
