import Link from 'next/link';
import Image from 'next/image';
import Hero from './Hero/Hero';
import Prices from './Prices/Prices';
import { GuestMascot } from './GuestMascot';

const benefits = [
  { number: '01', title: 'Предложения рядом', detail: 'Ищите запчасти среди подключённых магазинов в одном интерфейсе.' },
  { number: '02', title: 'Цены в одном списке', detail: 'Сравнивайте доступные предложения и переходите к продавцу.' },
  { number: '03', title: 'Меньше ручного поиска', detail: 'Фильтры и карточки помогают быстрее выбрать подходящую деталь.' },
];

export const HomeWidget: React.FC = () => (
  <main className="guest-home overflow-hidden bg-ivory">
    <Hero />
    <section id="compare" className="guest-section relative flex items-center border-t border-border-light-subtle py-20">
      <Image src="/redesign/spray-wide.png" alt="" aria-hidden="true" width={2172} height={724} unoptimized className="guest-spray absolute -right-52 -top-12 w-[900px] rotate-180" />
      <div className="relative mx-auto grid w-full max-w-[1200px] items-center gap-12 px-6 lg:grid-cols-[.9fr_1.1fr]">
        <div><p className="mb-4 text-sm font-semibold uppercase tracking-[.15em] text-positive">Сравнение цен</p><h2 className="text-[clamp(2.75rem,5vw,5rem)] font-bold leading-[1.05] tracking-[-.045em] text-slate">Магазины в одном поиске</h2><p className="mt-6 max-w-[48ch] text-lg text-body-subtle">Находите предложения подключённых магазинов и сравнивайте цену, наличие и состояние товара в результатах поиска.</p><Link href="/register" className="btn-primary mt-8">Начать поиск</Link></div>
        <div className="guest-glass grid gap-3 rounded-[30px] p-6 sm:grid-cols-2 sm:p-9" aria-label="Подключённые магазины">
          {['Профи', 'Либерти', 'Дивизион', 'ТГСМ'].map((shop) => <div key={shop} className="flex min-h-24 items-center justify-center rounded-[18px] border border-border-light-subtle bg-ivory/75 px-5 text-xl font-semibold text-slate">{shop}</div>)}
        </div>
      </div>
    </section>
    <section id="advantages" className="guest-section relative flex items-center py-20">
      <Image src="/redesign/spray-corner.png" alt="" aria-hidden="true" width={1536} height={1024} unoptimized className="guest-spray absolute -bottom-24 -left-64 w-[650px]" />
      <div className="mx-auto grid w-full max-w-[1200px] items-center gap-7 px-6 lg:grid-cols-[280px_1fr]">
        <GuestMascot pose="calm" className="mx-auto hidden max-h-[510px] lg:block" />
        <div><p className="mb-4 text-sm font-semibold uppercase tracking-[.15em] text-positive">Преимущества</p><h2 className="mb-10 text-[clamp(2.75rem,5vw,5rem)] font-bold leading-[1.05] tracking-[-.045em] text-slate">Больше ясности при выборе</h2><div className="grid gap-4 md:grid-cols-3">{benefits.map((benefit) => <article key={benefit.number} className="guest-glass min-h-[260px] rounded-[26px] p-7"><span className="text-sm font-bold text-positive">{benefit.number}</span><h3 className="mt-12 text-xl font-bold text-slate">{benefit.title}</h3><p className="mt-3 text-sm leading-relaxed text-body-subtle">{benefit.detail}</p></article>)}</div></div>
      </div>
    </section>
    <section id="how-it-works" className="guest-section relative flex items-center py-20">
      <Image src="/redesign/spray-corner.png" alt="" aria-hidden="true" width={1536} height={1024} unoptimized className="guest-spray absolute -right-64 -top-16 w-[650px] rotate-180" />
      <div className="mx-auto grid w-full max-w-[1200px] items-center gap-8 px-6 lg:grid-cols-[1fr_280px]">
        <div><p className="mb-4 text-sm font-semibold uppercase tracking-[.15em] text-positive">Три шага</p><h2 className="mb-10 text-[clamp(2.75rem,5vw,5rem)] font-bold leading-[1.05] tracking-[-.045em] text-slate">Как это работает</h2><ol className="grid gap-4 md:grid-cols-3">{['Введите запрос', 'Сравните предложения', 'Перейдите в магазин'].map((step, index) => <li key={step} className="guest-glass min-h-[190px] rounded-[26px] p-7"><span className="flex h-10 w-10 items-center justify-center rounded-full bg-accent font-bold text-white">{index + 1}</span><h3 className="mt-9 text-xl font-semibold text-slate">{step}</h3></li>)}</ol></div>
        <GuestMascot pose="pointing" mirrored className="mx-auto hidden max-h-[500px] lg:block" />
      </div>
    </section>
    <Prices />
    <section id="start" className="guest-section relative flex items-center overflow-hidden py-20"><Image src="/redesign/spray-corner.png" alt="" aria-hidden="true" width={1536} height={1024} unoptimized className="guest-spray absolute -right-40 bottom-0 w-[650px]" /><div className="relative mx-auto grid w-full max-w-[1200px] items-center gap-12 px-6 lg:grid-cols-[320px_1fr]"><GuestMascot pose="presenting" className="mx-auto hidden max-h-[550px] lg:block" /><div><p className="mb-4 text-sm font-semibold uppercase tracking-[.15em] text-positive">Начните с поиска</p><h2 className="text-[clamp(2.75rem,5vw,5rem)] font-bold leading-[1.05] tracking-[-.045em] text-slate">Найдите нужную запчасть</h2><p className="mt-6 max-w-[48ch] text-lg text-body-subtle">Создайте аккаунт, чтобы искать и сравнивать предложения магазинов.</p><Link href="/register" className="btn-primary mt-8">Найти запчасть</Link></div></div></section>
  </main>
);
