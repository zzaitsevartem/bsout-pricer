'use client';

import Link from 'next/link';
import { useUnit } from 'effector-react';
import { $isAuth } from '@/models/auth';
import { useProductSearch } from '@/models/product';

function formatPrice(raw: string): string {
  const num = parseFloat(raw);
  if (isNaN(num)) return raw;
  return num.toLocaleString('ru-RU') + ' ₽';
}

const staticProducts = [
  { name: 'Дисплей iPhone 13', price: 4500, bar: 'fill-slate', cheap: true },
  { name: 'Аккумулятор Samsung', price: 1890, bar: 'fill-clay', cheap: false },
  { name: 'Материнская плата', price: 8200, bar: 'fill-slate', cheap: false },
  { name: 'Шлейф зарядки', price: 650, bar: 'fill-clay', cheap: false },
];

export default function Dashboard() {
  const isAuth = useUnit($isAuth);

  const { data, isLoading } = useProductSearch(
    { q: '', page: 1, per_page: 4, sort_by: 'updated' },
    { enabled: isAuth },
  );

  const products = data?.results ?? null;
  const minPrice = products && products.length > 0
    ? Math.min(...products.map((p) => parseFloat(p.price)))
    : null;

  return (
    <section className="bg-ivory py-[84px] max-md:py-[61px] max-[480px]:py-[48px]">
      <div className="max-w-[1200px] mx-auto px-6">
        <div className="grid grid-cols-[55%_45%] gap-12 items-center max-md:grid-cols-1">
          <div>
            <p className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted mb-2">Дашборд</p>
            <h2 className="text-[40px] font-semibold leading-[1.15] tracking-[-0.01em] mb-6 text-slate">
              Вся информация в одном окне
            </h2>
            <p className="text-lg leading-[1.4] text-body max-w-[64ch] mb-4">
              Удобная таблица с ценами, фильтрами и историей изменений. Самое дешёвое предложение выделяется автоматически.
            </p>
            <Link href={isAuth ? '/search' : '/register'} className="btn-arrow">
              {isAuth ? 'Перейти к поиску' : 'Посмотреть в деле'}
            </Link>
          </div>
          <div className="bg-ivory-warm rounded-[24px] p-6 min-h-[340px] border border-[#E3DACC] flex flex-col gap-4">
            <div className="flex gap-3 items-center p-3 bg-slate text-ivory">
              <span className="text-[13px] font-semibold flex-1">Товар</span>
              <span className="flex-[0_0_60px] h-2 bg-slate" />
              <span className="text-[13px] w-20 text-right font-montserrat">Цена</span>
            </div>

            {isLoading && (
              <div className="flex-1 flex items-center justify-center text-body-muted text-[14px]">
                Загрузка...
              </div>
            )}

            {!isLoading && products && products.map((p) => {
              const priceNum = parseFloat(p.price);
              const isCheapest = minPrice !== null && priceNum === minPrice;
              return (
                <div key={p.id} className="flex gap-3 items-center p-3 bg-ivory">
                  <span className="text-[14px] flex-1 text-slate truncate">{p.name}</span>
                  <div className="flex gap-1 flex-1">
                    <span className={`h-2 flex-1 ${isCheapest ? 'bg-slate' : 'bg-clay'}`} />
                  </div>
                  <span className={`font-montserrat text-[14px] font-medium w-20 text-right ${isCheapest ? 'text-olive font-bold' : 'text-slate'}`}>
                    {formatPrice(p.price)}
                  </span>
                </div>
              );
            })}

            {!isLoading && !products && staticProducts.map((row) => (
              <div key={row.name} className="flex gap-3 items-center p-3 bg-ivory">
                <span className="text-[14px] flex-1 text-slate">{row.name}</span>
                <div className="flex gap-1 flex-1">
                  <span className={`h-2 flex-1 ${row.bar === 'fill-slate' ? 'bg-slate' : 'bg-clay'}`} />
                </div>
                <span className={`font-montserrat text-[14px] font-medium w-20 text-right ${row.cheap ? 'text-olive font-bold' : 'text-slate'}`}>
                  {row.price.toLocaleString('ru-RU')} ₽
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
