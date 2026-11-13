'use client';
import { useUnit } from 'effector-react';
import { $isAuth } from '@/shared/config/store';
import { useDeviceTrackingMutation, useTrackedDevices, useTrackingUsage } from '@/models/tracking';

export function DeviceTrackButton({ id, name }: { id: number; name: string }) {
  const isAuth = useUnit($isAuth);
  const usage = useTrackingUsage({ enabled: isAuth });
  const enabled = isAuth && usage.data?.plan === 'advanced';
  const devices = useTrackedDevices(enabled);
  const mutation = useDeviceTrackingMutation();
  if (!enabled) return null;
  const tracked = devices.data?.some((device) => device.id === id) ?? false;
  return (
    <div className="py-4">
      <button
        className="btn-secondary btn-sm"
        disabled={devices.isPending || devices.isError || mutation.isPending}
        onClick={() => mutation.mutate({ id, remove: tracked })}
      >
        {tracked ? 'Перестать отслеживать устройство' : 'Отслеживать новые запчасти'}
      </button>
      {(devices.isError || mutation.isError) && (
        <p role="alert">Не удалось изменить отслеживание {name}. Попробуйте ещё раз.</p>
      )}
    </div>
  );
}
