import React from 'react';
import styles from './Carousel.module.scss';
import greenSpark from '../../../../shared/assets/images/greenSpark.webp';
import divizion from '../../../../shared/assets/images/divizion.webp';
import liberty from '../../../../shared/assets/images/liberty.webp';
import profi from '../../../../shared/assets/images/profi.webp';
import taggsm from '../../../../shared/assets/images/taggsm.webp';

const Carousel: React.FC = () => {
  const partners = [
    { id: 1, logo: greenSpark, alt: 'greenSpark-logo', url: 'https://green-spark.ru' },
    { id: 2, logo: taggsm, alt: 'taggsm-logo', url: 'https://taggsm.ru' },
    { id: 3, logo: divizion, alt: 'divizion-logo', url: 'https://divizion126.ru' },
    { id: 4, logo: liberty, alt: 'liberty-logo', url: 'https://liberti.ru' },
    { id: 5, logo: profi, alt: 'profi-logo', url: 'https://siriust.ru' },
  ];

  const infinitePartners = [...partners, ...partners, ...partners];

  return (
    <div className={styles.carouselWrapper}>
      <div className={styles.carousel}>
        {infinitePartners.map((partner, index) => (
          <a
            key={`${partner.id}-${index}`}
            href={partner.url}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.carouselItem}
          >
            <img src={partner.logo.src} alt={partner.alt} />
          </a>
        ))}
      </div>
    </div>
  );
};
export default Carousel;
