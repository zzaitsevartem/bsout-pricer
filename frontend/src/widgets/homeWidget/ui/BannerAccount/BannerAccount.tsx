import React from 'react';
import Link from 'next/link';

const BannerAccount: React.FC = () => {
  return (
    <section className="bg-ivory py-[84px] max-md:py-[61px] max-[480px]:py-[48px]">
      <div className="max-w-[1200px] mx-auto px-6">
        <div className="bg-ivory-warm rounded-[24px] p-12 text-center max-w-[800px] mx-auto max-md:p-8 max-[480px]:p-6">
          <h2 className="text-[40px] font-semibold leading-[1.15] tracking-[-0.01em] mb-4 text-slate max-md:text-[32px] max-[480px]:text-[28px]">
            Готовы найти нужную запчасть?
          </h2>
          <p className="text-lg leading-[1.4] text-body max-w-[50ch] mx-auto mb-8">
            Зарегистрируйтесь бесплатно и начните экономить время на поиске запчастей уже сегодня.
          </p>
          <Link href="/register" className="btn-primary btn-lg">Создать аккаунт</Link>
        </div>
      </div>
    </section>
  );
};

export default BannerAccount;
