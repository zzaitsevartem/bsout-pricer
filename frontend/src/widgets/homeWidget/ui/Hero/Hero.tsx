import Link from 'next/link';
import React from 'react';
import styles from './Hero.module.scss';
import { Arrow } from '../../../../shared/ui/IconSVG';
import figureCylinder from '../../../../shared/assets/images/figureCylinder.webp';
import figurePiramid from '../../../../shared/assets/images/figurePiramid.webp';
import figureHaifTorus from '../../../../shared/assets/images/figureHaifTorus.webp';

const Hero: React.FC = () => {
  return (
    <div className={styles.hero}>
      <div className={styles.prewew}>
        <p>Мгновенный поиск по тысячам предложений от проверенных магазинов</p>
      </div>
      <div className={styles.title}>
        <h1>Платформа <br /> для мониторинга цен</h1>
      </div>
      <div className={styles.content}>
        <p>Сервис анализирует цены на запчасти для телефонов, ноутбуков и другой<br />техники в реальном времени...</p>
      </div>
      <div className={styles.buttons}>
        <button className={styles.primaryButton}>Попробовать бесплатно</button>
        <Link href="/" className={styles.secondaryButton}>
          Подробнее <Arrow className={styles.arrowIcon} />
        </Link>
      </div>
      <div className={styles.images}>
        <img src={figureCylinder.src} alt="Цилиндр" className={styles.figureCylinder}/>
        <img src={figurePiramid.src} alt="Пирамида" className={styles.figurePiramid}/>
        <img src={figureHaifTorus.src} alt="Полуторус" className={styles.figureHaifTorus}/>
      </div>
    </div>
  );
};
export default Hero;
