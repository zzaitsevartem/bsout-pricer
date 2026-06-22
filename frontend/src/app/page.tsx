import { Header } from '../widgets/Header/ui/Header';
import { Footer } from '../widgets/Footer/ui/Footer';
import { HomeWidget } from '../widgets/homeWidget/ui';
import DecorativeLines from '../shared/ui/DecorativeLines';

export default function Home() {
  return (
    <>
      <DecorativeLines />
      <div className="relative z-10">
        <Header />
        <HomeWidget />
        <Footer />
      </div>
    </>
  );
}
