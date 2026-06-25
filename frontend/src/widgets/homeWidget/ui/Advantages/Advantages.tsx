import React from 'react';

const advantages = [
  {
    title: 'Актуальная информация',
    desc: 'Цены и наличие обновляются в реальном времени. Вы всегда видите актуальные предложения от всех магазинов.',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <circle cx="12" cy="12" r="10"/>
        <path d="M12 6v6l4 2"/>
      </svg>
    ),
  },
  {
    title: 'Гибкость поиска',
    desc: 'Точное совпадение, частичное совпадение и нечёткий поиск с автодополнением для продвинутого тарифа.',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M12 2L2 7l10 5 10-5-10-5z"/>
        <path d="M2 17l10 5 10-5"/>
        <path d="M2 12l10 5 10-5"/>
      </svg>
    ),
  },
  {
    title: 'Экономия времени',
    desc: 'Больше не нужно просматривать 5 сайтов. Один поиск — все предложения. Мгновенное сравнение цен.',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
      </svg>
    ),
  },
];

const Advantages: React.FC = () => {
  return (
    <section className="bg-ivory py-[84px] max-md:py-[61px] max-[480px]:py-[48px]">
      <div className="max-w-[1200px] mx-auto px-6">
        <div className="text-center mb-8">
          <p className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted mb-2">Преимущества</p>
          <h2 className="text-[40px] font-semibold leading-[1.15] tracking-[-0.01em] mb-6 text-slate">
            Почему выбирают BScout
          </h2>
          <p className="text-lg leading-[1.4] text-body max-w-[64ch] mx-auto">
            Единый интерфейс для поиска запчастей по всем магазинам города
          </p>
        </div>
        <div className="grid grid-cols-3 gap-6 max-md:grid-cols-1">
          {advantages.map((item) => (
            <div key={item.title} className="rounded-[24px] p-[31px] bg-ivory-elevated">
              <div className="w-12 h-12 bg-ivory-warm flex items-center justify-center text-slate mb-4">
                {item.icon}
              </div>
              <h4 className="text-xl leading-[1.4] mb-3 text-slate font-semibold">{item.title}</h4>
              <p className="text-[15px] leading-[1.4] text-body-subtle">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Advantages;
