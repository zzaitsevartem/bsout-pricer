import Link from 'next/link';
import React from 'react';

const Hero: React.FC = () => {
  return (
    <section className="bg-ivory py-[84px] max-md:py-[61px] max-[480px]:py-[48px]">
      <div className="max-w-[1200px] mx-auto px-6 grid grid-cols-[55%_45%] gap-12 items-start max-md:grid-cols-1 max-md:gap-8">
        <div>
          <h1 className="text-[61px] font-bold leading-[1.1] tracking-[-0.02em] mb-6 text-slate max-md:text-[44px] max-[480px]:text-[36px]">
            Поиск запчастей для{' '}
            <span className="underline underline-offset-[6px] decoration-3">электроники</span>{' '}
            в Ставрополе
          </h1>
          <p className="text-lg leading-[1.4] text-body mb-8 max-w-[50ch]">
            Сравнивайте цены на запчасти для телефонов, ноутбуков и электроники в 5 магазинах города. Находите самые выгодные предложения за секунды.
          </p>
          <div className="flex gap-4 items-center flex-wrap">
            <Link href="/register" className="btn-primary btn-lg">Начать бесплатно</Link>
            <Link href="/search" className="btn-arrow">Попробовать поиск</Link>
          </div>
        </div>
        <div className="flex justify-center items-center">
          <div className="w-full aspect-[4/3] bg-slate rounded-[24px] flex flex-col gap-4 p-12 items-start overflow-hidden">
            <div className="flex gap-2 w-full">
              <div className="h-8 flex-1 bg-white/10" />
              <div className="h-8 w-20 bg-white/15" />
            </div>
            <div className="flex flex-col gap-3 w-full mt-4">
              {[1, 2].map((i) => (
                <div key={i} className="flex gap-3 p-3 bg-white/5">
                  <div className="w-12 h-12 bg-white/10" />
                  <div className="flex-1">
                    <div className="h-[14px] w-[70%] bg-white/15 mb-[6px]" />
                    <div className="h-3 w-[40%] bg-white/10" />
                  </div>
                  <div className="text-right">
                    <div className="h-4 w-15 bg-white/20" />
                    <div className="h-3 w-10 bg-white/10 mt-1" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;
