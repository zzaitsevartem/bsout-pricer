import React from "react";
import Link from 'next/link';
import styles from './BannerAccount.module.scss';
import { Arrow } from '../../../../shared/ui/IconSVG';
import emojiStar from '../../../../shared/assets/images/emojiStar.webp';
import helixTwo from '../../../../shared/assets/images/helixTwo.webp';

const BannerAccount: React.FC = () => {
  return (
    <div className={styles.bannerAccount}>
      <div className={styles.title}>
        <h1>Получите доступ к личному<br />кабинету уже сегодня</h1>
        <h2>Экономьте на покупке запчастей с автоматическим отслеживанием цен...</h2>
      </div>
      <div className={styles.buttons}>
        <button className={styles.primaryButton}>Попробовать бесплатно</button>
        <Link href="/" className={styles.secondaryButton}>
          Подробнее <Arrow className={styles.arrowIcon} />
        </Link>
      </div>
      <div className={styles.images}>
        <img src={emojiStar.src} alt="emojiStar" className={styles.emojiStar} />
        <img src={helixTwo.src} alt="helixTwo" className={styles.helixTwo} />
      </div>
    </div>
  );
};
export default BannerAccount;
