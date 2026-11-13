'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { catalogApi } from '@/models/catalog';
import { ProductSearchField } from '@/widgets/ProductSearch/ui/ProductSearchField';
import { useDeviceTrackingMutation, useTrackedDevices } from '@/models/tracking';
import { RemoveTrackingDialog } from './RemoveTrackingDialog';
import { TrackingPreviewCard, TrackingPreviewRow } from './TrackingPreviewCard';

export function DeviceTracking() {
  const [removing, setRemoving] = useState<{ id: number; name: string } | null>(null);
  const [search, setSearch] = useState('');
  const [frequentError, setFrequentError] = useState(false);
  const [resolving, setResolving] = useState(false);
  const devices = useTrackedDevices(true);
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
                    className="min-w-0 flex-1 break-words text-[14px] text-slate transition-colors hover:text-olive"
                    href={`/devices/${encodeURIComponent(device.model_key)}`}
                  >
                    {device.name.toLocaleLowerCase().startsWith(device.brand.toLocaleLowerCase())
                      ? device.name
                      : `${device.brand} ${device.name}`}
                  </Link>
                  <button
                    className="w-20 flex-none rounded-lg px-2 py-2 text-right text-[14px] font-semibold text-clay transition-colors hover:bg-status-danger hover:text-clay-ember focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-clay"
                    disabled={mutation.isPending}
                    onClick={() => {
                      mutation.reset();
                      setRemoving({ id: device.id, name: device.name });
                    }}
                    aria-label={`Удалить ${device.name} из отслеживания`}
                  >
                    Удалить
                  </button>
                </TrackingPreviewRow>
              ))
            ) : (
              <div className="flex flex-1 items-center justify-center text-center">
                <p className="text-[15px] font-semibold text-body-muted">
                  Добавьте первое устройство
                </p>
              </div>
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
          <div className="field-shell flex items-center rounded-full border border-border-input bg-ivory p-[6px] pl-7 transition-colors focus-within:border-border-default">
            <ProductSearchField
              id="device-tracking-search"
              value={search}
              onValueChange={(value) => {
                setSearch(value);
                setFrequentError(false);
              }}
              onSelect={() => {}}
              onDeviceSelect={(device) =>
                mutation.mutate({ id: device.id }, { onSuccess: () => setSearch('') })
              }
              onFrequentSelect={async (device) => {
                if (resolving || mutation.isPending) return;
                setFrequentError(false);
                setResolving(true);
                try {
                  const response = await catalogApi.devices({ q: device.label, limit: 8 });
                  const match = response.data.find((item) => item.model_key === device.model_key);
                  if (!match) throw new Error('Device not found');
                  mutation.mutate({ id: match.id }, { onSuccess: () => setSearch('') });
                } catch {
                  setFrequentError(true);
                } finally {
                  setResolving(false);
                }
              }}
              deviceOnly
              label="Найти устройство"
              placeholder="Например, iPhone 15"
              className="flex-1"
              inputClassName="h-[52px] w-full min-w-0 border-none bg-transparent text-[18px] text-slate placeholder:text-body-muted focus:outline-none [&::-webkit-search-cancel-button]:appearance-none"
            />
          </div>
          {frequentError && <p role="alert">Не удалось найти устройство. Попробуйте ещё раз.</p>}
          {mutation.isError && (
            <p role="alert">Не удалось изменить отслеживание. Попробуйте ещё раз.</p>
          )}
        </div>
      </div>
      {removing && (
        <RemoveTrackingDialog
          name={removing.name}
          pending={mutation.isPending}
          error={mutation.isError}
          onCancel={() => setRemoving(null)}
          onConfirm={() =>
            mutation.mutate(
              { id: removing.id, remove: true },
              { onSuccess: () => setRemoving(null) },
            )
          }
        />
      )}
    </section>
  );
}
