import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { DeviceClient } from './DeviceClient';
import { DeviceOverview } from './DeviceOverview';
import type { Device } from '@/models/device';
const { query } = vi.hoisted(() => ({ query: vi.fn() }));
vi.mock('@/widgets/authorizedHome/ui/DeviceTrackButton', () => ({ DeviceTrackButton: () => null }));
vi.mock('@/models/device', () => ({ useDevice: query }));
vi.mock('@/app/search/_components/SearchClient', () => ({
  SearchClient: ({ device }: { device: Device }) => <p>Каталог {device.name}</p>,
}));
const device: Device = {
  id: 7,
  model_key: 'samsung-s20',
  name: 'Galaxy S20',
  brand: { id: 1, name: 'Samsung', slug: 'samsung' },
  aliases: [],
  model_codes: ['SM-G980F'],
  release_year: 2020,
  images: [
    {
      url: 'https://example.com/phone.jpg',
      source_name: 'Commons',
      source_url: 'https://example.com/source',
      license: 'CC BY-SA',
      attribution: 'Author',
    },
    {
      url: 'https://example.com/back.jpg',
      source_name: 'Commons',
      source_url: 'https://example.com/source2',
      license: null,
      attribution: null,
    },
  ],
  metadata_source_url: null,
};
describe('device page', () => {
  it('renders sourced device gallery, known specs and visible categories', () => {
    render(<DeviceOverview device={device} categories={<button>Все 12</button>} />);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      'Запчасти и аксессуары для Samsung Galaxy S20',
    );
    expect(screen.getByText('SM-G980F')).toBeVisible();
    expect(screen.getByRole('link', { name: 'Commons · CC BY-SA' })).toHaveAttribute(
      'href',
      'https://example.com/source',
    );
    fireEvent.click(screen.getByRole('button', { name: 'Фото 2' }));
    expect(screen.getByRole('img')).toHaveAttribute('src', 'https://example.com/back.jpg');
    fireEvent.error(screen.getByRole('img'));
    expect(screen.getByText('Фотография устройства пока недоступна')).toBeVisible();
    expect(screen.getByRole('button', { name: 'Все 12' })).toBeVisible();
  });
  it('handles absent photo and unknown metadata without inventing values', () => {
    render(
      <DeviceOverview device={{ ...device, images: [], model_codes: [], release_year: null }} />,
    );
    expect(screen.getByText('Характеристики устройства пока не добавлены.')).toBeVisible();
    expect(screen.getByText('Фотография устройства пока недоступна')).toBeVisible();
  });
  it('retries API errors and distinguishes a missing device', () => {
    const refetch = vi.fn();
    query.mockReturnValue({ isError: true, error: new Error(), refetch });
    const { rerender } = render(<DeviceClient modelKey="bad" />);
    fireEvent.click(screen.getByRole('button', { name: 'Повторить' }));
    expect(refetch).toHaveBeenCalledOnce();
    query.mockReturnValue({
      isError: true,
      error: { isAxiosError: true, response: { status: 404 } },
      refetch,
    });
    rerender(<DeviceClient modelKey="missing" />);
    expect(screen.getByRole('heading')).toHaveTextContent('Устройство не найдено');
    expect(screen.queryByRole('button', { name: 'Повторить' })).not.toBeInTheDocument();
  });
  it('does not render old catalog while loading another model', () => {
    query.mockReturnValue({ isPending: true });
    render(<DeviceClient modelKey="xiaomi" />);
    expect(screen.getByRole('status')).toHaveTextContent('Загрузка устройства');
    expect(screen.queryByText(/Каталог/)).not.toBeInTheDocument();
  });
});
