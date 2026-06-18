import React from 'react';
import styles from './Advantages.module.scss';
import vurtel from '../../../../shared/assets/images/vurtel.webp';
import cube from '../../../../shared/assets/images/cube.webp';
import helix from '../../../../shared/assets/images/helix.webp';

const Advantages: React.FC = () => {
  return (
    <div className={styles.advantages}>
      <div className={styles.title}>
        <h1>Почему выбирают<br />BScout?</h1>
        <h2>Получайте ежедневные отчеты с актуализированной<br />информацией в личном кабинете</h2>
      </div>
      <div className={styles.blocks}>
        <div className={styles.blockItem}>
          <img src={helix.src} alt='helix' />
          <h1>Актуальная информация</h1>
          <p>Система ежедневно обновляет данные...</p>
        </div>
        <div className={styles.blockItem}>
          <img src={vurtel.src} alt='vurtel' />
          <h1>Гибкость</h1>
          <p>Адаптивные решения для разных потребностей и бюджета</p>
        </div>
        <div className={styles.blockItem}>
          <img src={cube.src} alt='cube' />
          <h1>Экономия времени</h1>
          <p>Автоматизация исключает ручной мониторинг...</p>
        </div>
      </div>
    </div>
  );
};
export default Advantages;
