import Image from 'next/image';
import heroLight from '@/shared/assets/images/heroSearchLens-light.png';
import heroDark from '@/shared/assets/images/heroSearchLens-dark.png';

/** Shared themed artwork; on small screens only the empty canvas is cropped. */
export function HeroArtwork() {
  return (
    <>
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 z-0 hidden overflow-hidden mix-blend-multiply dark:mix-blend-normal lg:block"
      >
        <div className="relative mx-auto h-full max-w-[1280px]">
          <Image
            src={heroLight}
            alt=""
            fill
            priority
            quality={95}
            sizes="(min-width: 1280px) 1280px, 100vw"
            className="object-contain dark:hidden"
          />
          <Image
            src={heroDark}
            alt=""
            fill
            priority
            quality={95}
            sizes="(min-width: 1280px) 1280px, 100vw"
            className="hidden object-contain dark:block"
          />
        </div>
      </div>
      <div
        aria-hidden="true"
        className="pointer-events-none relative mx-auto mt-8 aspect-[1.1] w-full max-w-[420px] overflow-hidden mix-blend-multiply dark:mix-blend-normal lg:hidden"
      >
        <Image
          src={heroLight}
          alt=""
          width={1672}
          height={941}
          priority
          quality={95}
          sizes="(min-width: 768px) 1143px, 272vw"
          className="absolute -left-[154%] -top-[36%] h-auto w-[272%] max-w-none dark:hidden"
        />
        <Image
          src={heroDark}
          alt=""
          width={1672}
          height={941}
          priority
          quality={95}
          sizes="(min-width: 768px) 1143px, 272vw"
          className="absolute -left-[154%] -top-[36%] hidden h-auto w-[272%] max-w-none dark:block"
        />
      </div>
    </>
  );
}
