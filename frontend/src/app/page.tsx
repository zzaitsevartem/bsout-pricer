import { Header } from '../widgets/Header/ui/Header';
import { Footer } from '../widgets/Footer/ui/Footer';
import { HomeWidget } from '../widgets/homeWidget/ui';

export default function Home() {
  return (
    <>
      <Header />
      <HomeWidget />
      <Footer />
    </>
  );
}
