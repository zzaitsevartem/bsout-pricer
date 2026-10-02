import Link from 'next/link';
import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';

export const metadata = {
  title: 'Страница не найдена',
  robots: { index: false, follow: true },
};

export default function NotFoundPage() {
  return (
    <>
      <Header />
      <main className="bg-ivory">
        <div className="max-w-[1200px] mx-auto px-6 py-12 pb-16">
          <p className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted mb-2">
            Ошибка 404
          </p>
          <h1 className="text-[40px] font-semibold text-slate mb-4 max-md:text-[28px]">
            Страница не найдена
          </h1>

          <div className="max-w-[720px]">
            <p className="text-[16px] text-body leading-[1.5] mb-3">
              Такой страницы нет — возможно, её убрали, адрес набран с опечаткой или ссылка
              устарела.
            </p>
            <p className="text-[15px] text-body-subtle leading-[1.4] mb-8">
              Попробуйте начать с поиска: если нужного товара нет в подборке, он всё равно может
              быть в каталоге магазина.
            </p>
          </div>

          <div className="flex gap-3 flex-wrap">
            <Link href="/search" className="btn btn-primary btn-sm no-underline">
              К поиску
            </Link>
            <Link href="/tariffs" className="btn btn-secondary btn-sm no-underline">
              Тарифы
            </Link>
            <Link href="/" className="btn btn-ghost btn-sm no-underline">
              На главную
            </Link>
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}
