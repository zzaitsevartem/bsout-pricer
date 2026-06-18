import React from "react";
import styles from './Prices.module.scss';
import { CheckMark } from "../../../../shared/ui/IconSVG";

const Prices: React.FC = () => {
  return (
    <div className={styles.prices}>
      <div className={styles.title}>
        <h1>Следите за ценами на запчасти...</h1>
        <h2>Получайте актуальные данные...</h2>
      </div>
      <div className={styles.pricePlan}>
        <div className={`${styles.pricePlanItem} ${styles.light}`}>
          <h2>Пробный</h2>
          <div className={styles.price}>0 ₽ <span className={styles.period}>/ 3 дня</span></div>
          <button className={styles.registerButton}>Регистрация</button>
          <ul className={styles.features}>
            <li><CheckMark className={styles.checkIcon} /> Мониторинг до 10 товаров</li>
            <li><CheckMark className={styles.checkIcon} /> 2 поставщика для сравнения</li>
            <li><CheckMark className={styles.checkIcon} /> Обновление данных раз в 24 часа</li>
            <li><CheckMark className={styles.checkIcon} /> Базовые уведомления</li>
            <li><CheckMark className={styles.checkIcon} /> Доступ к истории цен за 1 месяц</li>
          </ul>
        </div>
        <div className={`${styles.pricePlanItem} ${styles.dark}`}>
          <h2>Базовый</h2>
          <div className={styles.price}>400 ₽ <span className={styles.period}>/ месяц</span></div>
          <button className={styles.registerButton}>Регистрация</button>
          <ul className={styles.features}>
            <li><CheckMark className={styles.checkIcon} /> Мониторинг до 100 товаров</li>
            <li><CheckMark className={styles.checkIcon} /> 15+ поставщиков для сравнения</li>
            <li><CheckMark className={styles.checkIcon} /> Обновление данных каждые 6 часов</li>
            <li><CheckMark className={styles.checkIcon} /> Приоритетные уведомления</li>
            <li><CheckMark className={styles.checkIcon} /> Доступ к истории цен за 6 месяцев</li>
            <li><CheckMark className={styles.checkIcon} /> Экспорт отчетов в PDF/CSV</li>
            <li><CheckMark className={styles.checkIcon} /> Круглосуточная поддержка</li>
          </ul>
        </div>
        <div className={`${styles.pricePlanItem} ${styles.light}`}>
          <h2>Продвинутый</h2>
          <div className={styles.price}>900 ₽ <span className={styles.period}>/ месяц</span></div>
          <button className={styles.registerButton}>Регистрация</button>
          <ul className={styles.features}>
            <li><CheckMark className={styles.checkIcon} /> Неограниченное количество товаров</li>
            <li><CheckMark className={styles.checkIcon} /> 50+ поставщиков для сравнения</li>
            <li><CheckMark className={styles.checkIcon} /> Обновление данных в реальном времени</li>
            <li><CheckMark className={styles.checkIcon} /> Пользовательские уведомления и отчеты</li>
            <li><CheckMark className={styles.checkIcon} /> Полная история цен (12+ месяцев)</li>
            <li><CheckMark className={styles.checkIcon} /> Расширенная аналитика</li>
            <li><CheckMark className={styles.checkIcon} /> Индивидуальный менеджер</li>
            <li><CheckMark className={styles.checkIcon} /> Круглосуточная поддержка</li>
            <li><CheckMark className={styles.checkIcon} /> API-доступ</li>
          </ul>
        </div>
      </div>
    </div>
  );
};
export default Prices;
