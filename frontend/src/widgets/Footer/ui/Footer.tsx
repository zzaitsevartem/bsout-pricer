import React from "react";
import Link from "next/link";
import styles from './Footer.module.scss';
import { LogoB, TgIcon, VkIcon } from '../../../shared/ui/IconSVG';

const Footer: React.FC = () => {
  return (
    <footer className={styles.footer}>
      <div className={styles.logo}>
        <Link href="/"><LogoB /></Link>
        <p>Мгновенный поиск по тысячам<br />предложений от проверенных<br />магазинов</p>
      </div>
      <div className={styles.links}>
        <div>
          <h3>Продукт</h3>
          <Link href="/integration">Интеграция</Link>
          <Link href="/faq">FAQ</Link>
          <Link href="/pricing">Тарифы</Link>
        </div>
        <div>
          <h3>Компания</h3>
          <Link href="/about">О нас</Link>
          <Link href="/blog">Блог</Link>
          <Link href="/careers">Вакансии</Link>
          <Link href="/contacts">Контакты</Link>
        </div>
        <div>
          <h3>Правовая информация</h3>
          <Link href="/privacy">Политика конфиденциальности</Link>
          <Link href="/terms">Условия пользования</Link>
          <Link href="/security">Безопасность данных</Link>
        </div>
      </div>
      <div className={styles.contacts}>
        <div className={styles.social}>
          <a href="https://t.me/ssaxharniyy" target="_blank" rel="noopener noreferrer"><TgIcon /></a>
          <a href="https://vk.com/ssaxharniyy" target="_blank" rel="noopener noreferrer"><VkIcon /></a>
        </div>
        <div className={styles.contactInfo}>
          <a href="tel:+79188613561">+7 (918) 861-35-61</a>
          <a href="mailto:bscout.pricer@yandex.ru">bscout.pricer@yandex.ru</a>
        </div>
      </div>
    </footer>
  );
};
export { Footer };
