import Link from 'next/link';
import { HeroArtwork } from '@/shared/ui/HeroArtwork';

const Hero: React.FC = () => {
  return (
    <section className="relative isolate bg-ivory">
      <div className="mx-auto flex min-h-[656px] max-w-[1280px] flex-col justify-center px-6 py-12 lg:py-14">
        <div className="relative z-[1] min-w-0 lg:max-w-[54%]">
          <h1 className="mb-6 text-[44px] font-bold leading-[1.1] tracking-[-0.02em] text-slate max-[480px]:text-[36px] lg:text-[48px] xl:text-[54px]">
            Поиск запчастей
            <br />
            для{' '}
            <span className="underline decoration-[3px] underline-offset-[6px]">электроники</span>
            <br />в Ставрополе
          </h1>
          <p className="mb-8 max-w-[50ch] text-lg leading-[1.4] text-body">
            Сравнивайте цены на запчасти для телефонов, ноутбуков и электроники в магазинах города.
            Находите самые выгодные предложения за секунды.
          </p>
          <div className="flex flex-wrap items-center gap-4">
            <Link href="/register" className="btn-primary btn-lg">
              Начать бесплатно
            </Link>
            <Link href="/search" className="btn-arrow">
              Попробовать поиск
            </Link>
          </div>
        </div>

        <HeroArtwork />
      </div>
    </section>
  );
};

export default Hero;
