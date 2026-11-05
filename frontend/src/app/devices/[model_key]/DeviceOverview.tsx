'use client';
import { useState, type ReactNode } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import type { Device } from '@/models/device';
import { cn } from '@/shared/lib/utils';
export function DeviceOverview({ device, categories }: { device: Device; categories?: ReactNode }) {
  const [selected, setSelected] = useState(0);
  const [failed, setFailed] = useState<string[]>([]);
  const image = device.images[selected];
  const title = device.name.toLocaleLowerCase().startsWith(device.brand.name.toLocaleLowerCase())
    ? device.name
    : `${device.brand.name} ${device.name}`;
  return (
    <section className="search-palette mx-auto max-w-[1200px] px-6 pt-8">
      <nav
        aria-label="Хлебные крошки"
        className="mb-6 flex flex-wrap gap-2 text-sm text-body-subtle"
      >
        <Link href="/">Главная</Link>
        <span aria-hidden="true">/</span>
        <Link href="/search">Поиск</Link>
        <span aria-hidden="true">/</span>
        <span aria-current="page">{title}</span>
      </nav>
      <h1 className="mb-8 text-2xl font-bold text-slate md:text-3xl">
        Запчасти и аксессуары для {title}
      </h1>
      <div className="grid min-w-0 gap-8 md:grid-cols-[minmax(0,320px)_minmax(0,1fr)]">
        <div className="min-w-0">
          <div className="relative flex h-72 items-center justify-center rounded-2xl border border-border-light-subtle bg-ivory-elevated p-6">
            {image && !failed.includes(image.url) ? (
              <Image
                unoptimized
                src={image.url}
                width={280}
                height={240}
                alt={title}
                className="h-full w-full object-contain"
                onError={() => setFailed((urls) => [...urls, image.url])}
              />
            ) : (
              <p className="text-center text-body-muted">Фотография устройства пока недоступна</p>
            )}
          </div>
          {device.images.length > 1 && (
            <div aria-label="Фотографии устройства" className="mt-3 flex flex-wrap gap-2">
              {device.images.map((photo, index) => (
                <button
                  key={photo.url}
                  aria-label={`Фото ${index + 1}`}
                  aria-pressed={selected === index}
                  onClick={() => setSelected(index)}
                  className={cn(
                    'rounded-xl border px-4 py-2 text-sm text-slate',
                    selected === index
                      ? 'border-accent bg-accent/10'
                      : 'border-border-light-subtle',
                  )}
                >
                  {index + 1}
                </button>
              ))}
            </div>
          )}
          {image && (
            <p className="mt-3 break-words text-xs text-body-muted">
              <a className="underline" href={image.source_url} target="_blank" rel="noreferrer">
                {image.source_name}
                {image.license ? ` · ${image.license}` : ''}
              </a>
              {image.attribution && ` · ${image.attribution}`}
            </p>
          )}
        </div>
        <div className="min-w-0">
          <h2 className="text-xl font-semibold text-slate">{title}</h2>
          <dl className="my-5 space-y-3 text-sm text-body-subtle">
            <div>
              <dt className="inline font-medium">Бренд: </dt>
              <dd className="inline">{device.brand.name}</dd>
            </div>
            {device.release_year && (
              <div>
                <dt className="inline font-medium">Год выпуска: </dt>
                <dd className="inline">{device.release_year}</dd>
              </div>
            )}
            {device.model_codes.length > 0 && (
              <div>
                <dt className="inline font-medium">Модельные коды: </dt>
                <dd className="inline break-words">{device.model_codes.join(', ')}</dd>
              </div>
            )}
          </dl>
          {!device.release_year && device.model_codes.length === 0 && (
            <p className="mb-5 text-sm text-body-muted">
              Характеристики устройства пока не добавлены.
            </p>
          )}
          {device.metadata_source_url && (
            <a
              href={device.metadata_source_url}
              target="_blank"
              rel="noreferrer"
              className="text-sm text-body-subtle underline"
            >
              Источник характеристик
            </a>
          )}
          <h2 className="mb-3 mt-6 text-lg font-semibold text-slate">Категории запчастей</h2>
          {categories ?? (
            <p className="text-sm text-body-subtle">
              Войдите, чтобы увидеть категории и сравнить цены.
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
