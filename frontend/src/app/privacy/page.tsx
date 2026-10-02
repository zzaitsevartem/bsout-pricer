import type { Metadata } from 'next';
import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';

export const metadata: Metadata = {
  title: 'Политика конфиденциальности',
  description: 'Какие данные собирает BScout, зачем они нужны и как их удалить.',
};

const OPERATOR_TODO = '[УКАЗАТЬ: наименование оператора, ИНН, адрес, контактный email]';

const sections: { heading: string; body: string[] }[] = [
  {
    heading: '1. Какие данные мы собираем',
    body: [
      'При регистрации: адрес электронной почты, имя, по желанию — логин, телефон и название компании. Пароль хранится только в виде необратимого хеша.',
      'При использовании сервиса: история поисковых запросов, список отслеживаемых товаров, история платежей и подписок, технические данные для безопасности (IP-адрес, данные сессии).',
    ],
  },
  {
    heading: '2. Зачем нужны данные',
    body: [
      'Доступ к поиску и сравнению цен, оформление и продление подписки, уведомления о снижении цены, защита аккаунта и предотвращение злоупотреблений.',
    ],
  },
  {
    heading: '3. Оплата',
    body: [
      'Оплата тарифов проходит через платёжный сервис ЮKassa. Данные банковских карт нам не передаются и у нас не хранятся.',
    ],
  },
  {
    heading: '4. Хранение и удаление',
    body: [
      'Данные хранятся, пока активен аккаунт. Токены доступа живут 15 минут, токены обновления — 30 дней и могут быть отозваны. Для удаления аккаунта и всех связанных данных напишите на support@bscout.ru — удалим в разумный срок, кроме данных, которые обязаны хранить по закону.',
    ],
  },
  {
    heading: '5. Передача третьим лицам',
    body: [
      'Не продаём и не передаём данные в рекламных целях. Передаём только то, что нужно для работы сервиса: платёжному сервису — данные платежа, почтовому провайдеру — адрес для писем.',
    ],
  },
  {
    heading: '6. Cookies и локальное хранилище',
    body: [
      'Сервис использует локальное хранилище браузера для токенов входа. Отдельной рекламной аналитики с cookies сейчас нет.',
    ],
  },
  {
    heading: '7. Оператор данных',
    body: [OPERATOR_TODO],
  },
];

export default function PrivacyPage() {
  return (
    <>
      <Header />
      <div className="max-w-[1200px] mx-auto px-6 py-12 pb-16">
        <div className="flex items-center gap-2 text-[14px] text-body-muted mb-4 flex-wrap">
          <a href="/" className="text-body-subtle no-underline hover:text-slate hover:underline">
            Главная
          </a>
          <span className="text-body-muted">/</span>
          <span>Политика конфиденциальности</span>
        </div>

        <p className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted mb-2">
          Правовая информация
        </p>
        <h1 className="text-[40px] font-semibold text-slate mb-8">Политика конфиденциальности</h1>

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
