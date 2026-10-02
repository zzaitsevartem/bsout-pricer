import type { Metadata } from 'next';
import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';

export const metadata: Metadata = {
  title: 'Условия использования',
  description: 'Условия использования сервиса BScout: тарифы, оплата, отмена подписки.',
};

const OPERATOR_TODO = '[УКАЗАТЬ: наименование исполнителя, ИНН, адрес, контактный email]';

const sections: { heading: string; body: string[] }[] = [
  {
    heading: '1. Что такое BScout',
    body: [
      'BScout — сервис поиска и сравнения цен на запчасти для электроники в подключённых магазинах. Цены, наличие и описания принадлежат магазинам-источникам и могут отличаться от данных на их сайтах: перед покупкой проверяйте цену у продавца.',
    ],
  },
  {
    heading: '2. Тарифы',
    body: [
      'Пробный тариф: 7 дней бесплатно, предоставляется один раз после подтверждения почты.',
      'Базовый: 399 ₽ за 30 дней. Продвинутый: 499 ₽ за 30 дней. На первый платёж любого тарифа действует скидка 20%.',
      'Оплата тарифов проходит через платёжный сервис ЮKassa. Оплатить тариф можно только с подтверждённой почтой.',
    ],
  },
  {
    heading: '3. Отмена и возврат',
    body: [
      'Отменить подписку можно в любой момент в личном кабинете: автопродление отключится, а доступ сохранится до конца уже оплаченного периода.',
    ],
  },
  {
    heading: '4. Правила использования',
    body: [
      'Запрещены действия, нарушающие работу сервиса: автоматический сбор данных в обход интерфейса, подбор паролей, попытки оплаты чужими средствами. При нарушениях доступ может быть ограничен.',
    ],
  },
  {
    heading: '5. Ответственность',
    body: [
      'Сервис показывает данные магазинов «как есть». Мы не отвечаем за наличие товара, сроки доставки и действия продавцов, но стараемся поддерживать данные актуальными.',
    ],
  },
  {
    heading: '6. Исполнитель',
    body: [OPERATOR_TODO],
  },
];

export default function TermsPage() {
  return (
    <>
      <Header />
      <div className="max-w-[1200px] mx-auto px-6 py-12 pb-16">
        <div className="flex items-center gap-2 text-[14px] text-body-muted mb-4 flex-wrap">
          <a href="/" className="text-body-subtle no-underline hover:text-slate hover:underline">
            Главная
          </a>
          <span className="text-body-muted">/</span>
          <span>Условия использования</span>
        </div>

        <p className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted mb-2">
          Правовая информация
        </p>
        <h1 className="text-[40px] font-semibold text-slate mb-8">Условия использования</h1>

        <div className="max-w-[800px]">
          {sections.map((section) => (
            <section key={section.heading} className="mb-8">
              <h2 className="text-[24px] font-semibold text-slate mb-3">{section.heading}</h2>
              {section.body.map((paragraph, index) => (
                <p key={index} className="text-[15px] text-body leading-relaxed mb-3">
                  {paragraph}
                </p>
              ))}
            </section>
          ))}
        </div>
      </div>
      <Footer />
    </>
  );
}
