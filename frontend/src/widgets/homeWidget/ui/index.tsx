import Hero from './Hero/Hero';
import Carousel from './Carousel/Carousel';
import Advantages from './Advantages/Advantages';
import Dashboard from './Dashboard/Dashboard';
import Prices from './Prices/Prices';
import BannerAccount from './BannerAccount/BannerAccount';

export const HomeWidget: React.FC = () => {
  return (
    <>
      <Hero />
      <Carousel />
      <Advantages />
      <Dashboard />
      <Prices />
      <BannerAccount />
    </>
  );
};
