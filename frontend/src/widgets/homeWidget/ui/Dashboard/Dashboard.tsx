import React from 'react';
import styles from './Dashboard.module.scss';
import torus from '../../../../shared/assets/images/torus.webp';
import figurePiramid from '../../../../shared/assets/images/figurePiramid.webp';
import dashboard from '../../../../shared/assets/images/dashboard.webp';

const Dashboard: React.FC = () => {
  return (
    <div className={styles.dashboard}>
      <div className={styles.title}>
        <h1>Удобная работа<br />с дашбордами</h1>
        <h2>Все возможности, чтобы сделать анализ цен простым, наглядным и эффективным для бизнеса</h2>
      </div>
      <div className={styles.dashboardImage}>
        <img src={dashboard.src} alt='dasboard' />
      </div>
      <div className={styles.images}>
        <img src={torus.src} alt='torus' className={styles.torus} />
        <img src={figurePiramid.src} alt='figurePiramid' className={styles.figurePiramid} />
      </div>
    </div>
  );
};
export default Dashboard;
