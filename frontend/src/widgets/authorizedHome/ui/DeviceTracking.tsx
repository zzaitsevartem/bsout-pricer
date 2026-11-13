'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useCatalogDevices } from '@/models/catalog';
import { useDeviceTrackingMutation, useTrackedDevices } from '@/models/tracking';

export function DeviceTracking() {
  const [search, setSearch] = useState('');
  const devices = useTrackedDevices(true);
  const options = useCatalogDevices({ q: search, limit: 6 });
  const mutation = useDeviceTrackingMutation();
  return (
    <section className="pb-[84px] max-md:pb-[61px]" aria-label="Отслеживание устройств">
      <div className="mx-auto max-w-[1200px] px-6">
        <h2 className="mb-4 text-[40px] font-semibold leading-[1.15] text-slate max-md:text-[32px]">
          Отслеживание устройств
        </h2>
        <p className="mb-4 text-body">
          Выберите устройство, чтобы получать уведомления о новых запчастях в каталоге.
        </p>
        <label htmlFor="device-tracking-search" className="block mb-2 text-slate">
          Найти устройство
        </label>
        <input
          autoComplete="off"
          id="device-tracking-search"
          className="w-full rounded-xl border border-border-light bg-ivory p-3 text-slate"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Например, iPhone 15"
        />
        {search.trim().length >= 2 && options.isError && (
          <p role="alert">Не удалось найти устройства.</p>
        )}
        {search.trim().length >= 2 && options.data && (
          <ul className="mt-2 space-y-2">
            {options.data.map((device) => (
              <li key={device.id}>
                <button
                  className="btn-secondary btn-sm"
                  disabled={mutation.isPending}
                  onClick={() =>
                    mutation.mutate({ id: device.id }, { onSuccess: () => setSearch('') })
                  }
                >
                  {device.label} — добавить
                </button>
              </li>
            ))}
          </ul>
        )}
        {mutation.isError && (
          <p role="alert">Не удалось изменить отслеживание. Попробуйте ещё раз.</p>
        )}
        {devices.isPending ? (
          <p className="mt-4">Загрузка…</p>
        ) : devices.isError ? (
          <p role="alert" className="mt-4">
            Не удалось загрузить устройства.
          </p>
        ) : devices.data?.length ? (
          <ul className="mt-4 space-y-2">
            {devices.data.map((device) => (
              <li key={device.id} className="flex items-center gap-4 rounded-xl bg-ivory-warm p-4">
                <Link
                  className="flex-1 text-slate hover:underline"
                  href={`/devices/${encodeURIComponent(device.model_key)}`}
                >
                  {device.name.toLocaleLowerCase().startsWith(device.brand.toLocaleLowerCase())
                    ? device.name
                    : `${device.brand} ${device.name}`}
                </Link>
                <button
                  className="btn-secondary btn-sm"
                  disabled={mutation.isPending}
                  onClick={() => mutation.mutate({ id: device.id, remove: true })}
                  aria-label={`Удалить ${device.name} из отслеживания`}
                >
                  Удалить
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-4 text-body-muted">Вы пока не отслеживаете устройства.</p>
        )}
      </div>
    </section>
  );
}
