import React from 'react';
import Link from 'next/link';

const Dashboard: React.FC = () => {
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
            <Link href="/register" className="btn-arrow">Посмотреть в деле</Link>
          </div>
          <div className="bg-ivory-warm rounded-[24px] p-6 min-h-[340px] border border-[#E3DACC] flex flex-col gap-4">
            <div className="flex gap-3 items-center p-3 bg-slate text-ivory">
              <span className="text-[13px] font-semibold flex-1">Товар</span>
              <span className="flex-[0_0_60px] h-2 bg-slate" />
              <span className="text-[13px] w-20 text-right font-montserrat">Цена</span>
            </div>
            {[
              { name: 'Дисплей iPhone 13', price: '4 500 ₽', bar: 'fill-slate', cheap: true },
              { name: 'Аккумулятор Samsung', price: '1 890 ₽', bar: 'fill-clay', cheap: false },
              { name: 'Материнская плата', price: '8 200 ₽', bar: 'fill-slate', cheap: false },
              { name: 'Шлейф зарядки', price: '650 ₽', bar: 'fill-clay', cheap: false },
            ].map((row) => (
              <div key={row.name} className="flex gap-3 items-center p-3 bg-ivory">
                <span className="text-[14px] flex-1 text-slate">{row.name}</span>
                <div className="flex gap-1 flex-1">
                  <span className={`h-2 flex-1 ${row.bar === 'fill-slate' ? 'bg-slate' : 'bg-clay'}`} />
                </div>
                <span className={`font-montserrat text-[14px] font-medium w-20 text-right ${row.cheap ? 'text-olive font-bold' : 'text-slate'}`}>
                  {row.price}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default Dashboard;
