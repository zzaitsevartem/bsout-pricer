'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useCatalogDevices } from '@/models/catalog';
import { useDeviceTrackingMutation, useTrackedDevices } from '@/models/tracking';
import { TrackingPreviewCard, TrackingPreviewRow } from './TrackingPreviewCard';

export function DeviceTracking() {
  const [search, setSearch] = useState('');
  const devices = useTrackedDevices(true);
  const options = useCatalogDevices({ q: search, limit: 6 });
  const mutation = useDeviceTrackingMutation();
  return (
    <section
      className="py-[84px] max-md:py-[61px] max-[480px]:py-[48px]"
      aria-label="Отслеживание устройств"
    >
      <div className="mx-auto grid max-w-[1200px] grid-cols-[minmax(0,45fr)_minmax(0,55fr)] items-center gap-12 px-6 max-md:grid-cols-1 max-md:gap-8">
        <div className="max-md:order-2">
          <TrackingPreviewCard
            header={
              <>
                <span className="flex-1 text-[13px] font-semibold">Устройство</span>
                <span className="w-20 text-right font-montserrat text-[13px]">Действие</span>
              </>
            }
          >
            {devices.isPending ? (
              <p className="text-[14px] text-body-muted">Загрузка…</p>
            ) : devices.isError ? (
              <p role="alert" className="text-[14px] text-body-muted">
                Не удалось загрузить устройства.
              </p>
            ) : devices.data?.length ? (
              devices.data.map((device) => (
                <TrackingPreviewRow key={device.id}>
                  <Link
                    className="min-w-0 flex-1 break-words text-[14px] text-slate hover:underline"
                    href={`/devices/${encodeURIComponent(device.model_key)}`}
                  >
                    {device.name.toLocaleLowerCase().startsWith(device.brand.toLocaleLowerCase())
                      ? device.name
                      : `${device.brand} ${device.name}`}
                  </Link>
                  <button
                    className="w-20 flex-none text-right text-[14px] text-body-muted hover:text-slate"
                    disabled={mutation.isPending}
                    onClick={() => mutation.mutate({ id: device.id, remove: true })}
                    aria-label={`Удалить ${device.name} из отслеживания`}
                  >
                    Удалить
                  </button>
                </TrackingPreviewRow>
              ))
            ) : (
              <p className="text-[14px] text-body-muted">Вы пока не отслеживаете устройства.</p>
            )}
          </TrackingPreviewCard>
        </div>
        <div className="max-md:order-1">
          <p className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted mb-2">
            Отслеживание устройств
          </p>
          <h2 className="mb-6 text-[40px] font-semibold leading-[1.15] tracking-[-0.01em] text-slate max-md:text-[32px] max-[480px]:text-[28px]">
            Новые запчасти для ваших устройств
          </h2>
          <p className="mb-4 max-w-[64ch] text-lg leading-[1.4] text-body">
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
        </div>
      </div>
    </section>
  );
}
