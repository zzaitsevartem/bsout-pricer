'use client';
import Link from 'next/link';
import axios from 'axios';
import { useDevice } from '@/models/device';
import { SearchClient } from '@/app/search/_components/SearchClient';
export function DeviceClient({ modelKey }: { modelKey: string }) {
  const device = useDevice(modelKey);
  if (device.isPending)
    return (
      <p role="status" className="p-8 text-body-subtle">
        Загрузка устройства…
      </p>
    );
  if (device.isError) {
    const missing = axios.isAxiosError(device.error) && device.error.response?.status === 404;
    return (
      <main className="mx-auto max-w-[1200px] px-6 py-12">
        <h1 className="text-2xl font-bold text-slate">
          {missing ? 'Устройство не найдено' : 'Не удалось загрузить устройство'}
        </h1>
        <p className="my-4 text-body-subtle">
          {missing
            ? 'Проверьте ссылку или найдите другую модель.'
            : 'Попробуйте загрузить страницу ещё раз.'}
        </p>
        {!missing && (
          <button className="btn-secondary" onClick={() => device.refetch()}>
            Повторить
          </button>
        )}
        <Link href="/search" className="btn-ghost">
          Поиск устройств
        </Link>
      </main>
    );
  }
  return <SearchClient key={device.data.id} device={device.data} />;
}
