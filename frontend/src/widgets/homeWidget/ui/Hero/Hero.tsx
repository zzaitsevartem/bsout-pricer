'use client';

import { FormEvent, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { GuestMascot } from '../GuestMascot';

const examples = ['Дисплей iPhone 13', 'Аккумулятор Samsung', 'Шлейф зарядки'];

export default function Hero() {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const submit = (event: FormEvent) => { event.preventDefault(); router.push('/register'); };

  return (
    <section id="home" className="guest-section relative isolate flex items-center overflow-hidden bg-ivory">
      <Image src="/redesign/spray-corner.png" alt="" aria-hidden="true" width={1536} height={1024} unoptimized className="guest-spray absolute -right-36 -top-20 w-[750px] rotate-180" />
      <Image src="/redesign/spray-wide.png" alt="" aria-hidden="true" width={2172} height={724} unoptimized className="guest-spray absolute -bottom-24 -left-72 w-[1050px]" />
      <div className="relative mx-auto grid w-full max-w-[1280px] items-center gap-6 px-6 pb-16 pt-12 lg:grid-cols-[1.1fr_.9fr] lg:pb-24 lg:pt-16">
        <div className="relative z-10 max-w-[720px]">
          <p className="mb-6 text-sm font-semibold uppercase tracking-[.16em] text-positive">Поиск запчастей в Ставрополе</p>
          <h1 className="text-[clamp(3rem,6vw,6rem)] font-bold leading-[1.02] tracking-[-.055em] text-slate">Нужная запчасть. <span className="text-positive">Честная цена.</span></h1>
          <p className="mt-7 max-w-[53ch] text-lg leading-relaxed text-body-subtle">Сравнивайте предложения магазинов в одном поиске и выбирайте подходящую запчасть.</p>
          <form onSubmit={submit} role="search" className="guest-glass mt-9 flex max-w-[720px] flex-col gap-3 rounded-[26px] p-2 sm:flex-row">
            <label htmlFor="guest-hero-search" className="sr-only">Название запчасти</label>
            <input id="guest-hero-search" autoComplete="off" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Введите название запчасти" className="min-w-0 flex-1 rounded-full bg-transparent px-5 py-3 text-slate outline-none placeholder:text-body-muted focus-visible:ring-2 focus-visible:ring-accent" />
            <button type="submit" className="btn-primary shrink-0 px-7">Найти запчасть</button>
          </form>
          <div className="mt-5 flex flex-wrap items-center gap-2 text-sm text-body-muted"><span>Например:</span>{examples.map((example) => <Link key={example} href="/register" className="rounded-full border border-border-input px-3 py-1 text-body-subtle no-underline hover:border-accent hover:text-slate">{example}</Link>)}</div>
          <div className="mt-8 flex gap-5 text-sm"><a href="#how-it-works" className="font-semibold text-slate underline decoration-accent underline-offset-4">Как это работает ↓</a><Link href="/tariffs" className="font-semibold text-slate underline decoration-accent underline-offset-4">Тарифы</Link></div>
        </div>
        <div className="relative mx-auto flex w-full max-w-[450px] items-end justify-center lg:max-w-none"><GuestMascot pose="hero" mirrored className="max-h-[650px]" /></div>
      </div>
    </section>
  );
}
