import React from 'react';

const partners = ['ТГСМ', 'Профи', 'Либерти', 'ГринСпарк', 'Дивизион'];

const Carousel: React.FC = () => {
  return (
    <section className="overflow-hidden py-12">
      <div className="flex gap-12 animate-scroll w-fit hover:[animation-play-state:paused]">
        {[...partners, ...partners].map((name, i) => (
          <div
            key={`${name}-${i}`}
            className="flex-shrink-0 flex items-center justify-center h-12 px-8 text-lg font-semibold text-body-muted tracking-wider uppercase opacity-60"
          >
            {name}
          </div>
        ))}
      </div>
    </section>
  );
};

export default Carousel;
