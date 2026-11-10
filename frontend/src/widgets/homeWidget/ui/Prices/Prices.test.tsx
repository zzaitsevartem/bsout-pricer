import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { TariffPlans } from '@/widgets/TariffPlans';
import Prices from './Prices';

vi.mock('@/models/payment', () => ({
  usePlans: () => ({
    data: [
      {
        plan: 'basic',
        nameRu: 'Тестовый тариф',
        price: 731,
        firstPaymentPrice: 731,
        currency: 'RUB',
        durationDays: 30,
        trackedProducts: 19,
        stores: 4,
        fuzzySearch: false,
        priceAlerts: false,
        exportReports: false,
        supportRu: '—',
        featured: false,
        sortOrder: 1,
      },
    ],
    isLoading: false,
    isError: false,
  }),
}));

describe('homepage prices', () => {
  it('uses current API plan values and offers registration without annual billing', () => {
    render(<Prices />);
    expect(screen.getByText('Тестовый тариф')).toBeInTheDocument();
    expect(screen.getByText(/731 ₽/)).toBeInTheDocument();
    expect(screen.getByText(/30 дней/)).toBeInTheDocument();
    expect(screen.getByText('До 19 отслеживаемых товаров')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Выбрать/ })).toHaveAttribute(
      'href',
      '/register?plan=basic',
    );
    expect(screen.queryByRole('button', { name: /год|annual/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('switch', { name: /год|annual/i })).not.toBeInTheDocument();
  });

  it('keeps subscription selection available to other routes', () => {
    const select = vi.fn();
    render(<TariffPlans action="subscription" onSelect={select} />);
    fireEvent.click(screen.getByRole('button', { name: 'Оплатить Тестовый тариф' }));
    expect(select).toHaveBeenCalledWith('basic');
  });
});
