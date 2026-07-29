import { useMemo } from 'react';
import type { PriceHistoryResponse } from '@/models/product';

function formatShortDate(iso: string): string {
  const d = new Date(iso);
  const months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];
  return `${months[d.getMonth()]} ${d.getFullYear()}`;
}

function formatAxisDate(iso: string): string {
  const d = new Date(iso);
  const months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];
  return months[d.getMonth()];
}

function formatPrice(raw: string): string {
  const num = parseFloat(raw);
  if (isNaN(num)) return raw;
  return num.toLocaleString('ru-RU') + ' ₽';
}

const W = 500;
const H = 140;
const PAD = { top: 10, right: 10, bottom: 24, left: 10 };
const plotW = W - PAD.left - PAD.right;
const plotH = H - PAD.top - PAD.bottom;

type PriceHistoryChartProps = {
  data: PriceHistoryResponse[];
};

export function PriceHistoryChart({ data }: PriceHistoryChartProps) {
  const { points, minPrice, maxPrice, labels } = useMemo(() => {
    if (data.length === 0) {
      return { points: '', minPrice: 0, maxPrice: 0, labels: [] };
    }

    const prices = data.map((d) => parseFloat(d.price));
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const range = max - min || 1;

    const pts = data.map((d, i) => {
      const x = PAD.left + (i / Math.max(data.length - 1, 1)) * plotW;
      const y = PAD.top + plotH - ((parseFloat(d.price) - min) / range) * plotH;
      return `${x},${y}`;
    });

    // Show ~6 date labels
    const step = Math.max(1, Math.floor(data.length / 6));
    const lbls = data.filter((_, i) => i % step === 0 || i === data.length - 1);

    return { points: pts.join(' '), minPrice: min, maxPrice: max, labels: lbls };
  }, [data]);

  if (data.length === 0) return null;

  const lineColor = '#141413';
  const gradientId = 'price-gradient';

  return (
    <div>
      <div className="w-full h-[140px] bg-ivory-elevated rounded-[12px] relative overflow-hidden">
        <svg
          width="100%"
          height="100%"
          viewBox={`0 0 ${W} ${H}`}
          preserveAspectRatio="none"
          className="absolute inset-0"
        >
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={lineColor} stopOpacity="0.08" />
              <stop offset="100%" stopColor={lineColor} stopOpacity="0.02" />
            </linearGradient>
          </defs>

          {/* Area fill */}
          <polygon
            points={`${PAD.left},${PAD.top + plotH} ${points} ${PAD.left + plotW},${PAD.top + plotH}`}
            fill={`url(#${gradientId})`}
          />

          {/* Line */}
          <polyline
            points={points}
            fill="none"
            stroke={lineColor}
            strokeWidth="2"
            vectorEffect="non-scaling-stroke"
          />
        </svg>
      </div>

      {/* Axis labels */}
      <div className="flex justify-between mt-1">
        {labels.map((d, i) => (
          <span key={i} className="text-[12px] text-body-muted">
            {formatAxisDate(d.recorded_at)}
          </span>
        ))}
      </div>

      {/* Price range */}
      <div className="flex justify-between mt-1">
        <span className="text-[11px] text-body-muted">от {formatPrice(String(minPrice))}</span>
        <span className="text-[11px] text-body-muted">до {formatPrice(String(maxPrice))}</span>
      </div>
    </div>
  );
}
