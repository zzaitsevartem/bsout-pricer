import React from 'react';
import Image from 'next/image';

import taggsm from '@/shared/assets/images/taggsm.webp';
import profi from '@/shared/assets/images/profi.webp';
import liberty from '@/shared/assets/images/liberty.webp';
import greenSpark from '@/shared/assets/images/greenSpark.webp';
import divizion from '@/shared/assets/images/divizion.webp';

const partners = [
  { name: 'ТГСМ', src: taggsm.src, href: 'https://taggsm.ru' },
  { name: 'Профи', src: profi.src, href: 'https://siriust.ru' },
  { name: 'Либерти', src: liberty.src, href: 'https://liberti.ru' },
  { name: 'ГринСпарк', src: greenSpark.src, href: 'https://green-spark.ru' },
  { name: 'Дивизион', src: divizion.src, href: 'https://www.divizion126.ru' },
];

const duplicatedPartners = [...partners, ...partners, ...partners, ...partners];

const Carousel: React.FC = () => {
  return (
    <section className="overflow-hidden py-12 group/carousel">
      <div className="flex gap-12 animate-scroll w-fit group-hover/carousel:[animation-play-state:paused]">
        {duplicatedPartners.map((partner, i) => (
          <a
            key={`${partner.name}-${i}`}
            href={partner.href}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-shrink-0 flex items-center justify-center h-12 w-32"
          >
            <Image
              src={partner.src}
              alt={partner.name}
              width={128}
              height={48}
              className="h-full w-auto object-contain grayscale opacity-60 transition-all duration-300 hover:grayscale-0 hover:opacity-100"
            />
          </a>
        ))}
      </div>
    </section>
  );
};

export default Carousel;
