'use client';

import React from 'react';
import { useCatalogPriceHistory } from '@/models/catalog';
import { cn } from '@/shared/lib/utils';
import {
  apiErrorMessage,
  formatDayShort,
  formatMoneyValue,
  formatNumber,
  parseMoney,
  plural,
} from '@/app/product/[id]/_components/lib';

const PERIODS = [30, 90, 180] as const;

const WIDTH = 640;
const HEIGHT = 200;
const PAD_LEFT = 72;
const PAD_RIGHT = 16;
const PAD_TOP = 16;
const PAD_BOTTOM = 30;
const INNER_WIDTH = WIDTH - PAD_LEFT - PAD_RIGHT;
const INNER_HEIGHT = HEIGHT - PAD_TOP - PAD_BOTTOM;
const BASELINE = PAD_TOP + INNER_HEIGHT;

type SeriesPoint = {
  day: string;
  value: number;
  stores: number;
};

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-[24px] border border-border-light bg-ivory-elevated p-6 text-[15px] text-body-subtle">
      {text}
    </div>
  );
}

type PriceHistoryProps = {
  productId: number;
};

export function PriceHistory({ productId }: PriceHistoryProps) {
  const [days, setDays] = React.useState<number>(90);
  const history = useCatalogPriceHistory(productId, days);

  const series: SeriesPoint[] = React.useMemo(() => {
    const points = history.data?.points ?? [];
    return points
      .map((point) => ({
        day: point.day,
        value: parseMoney(point.min_price_retail),
        stores: point.stores_count,
      }))
      .filter((point): point is SeriesPoint => point.value !== null);
  }, [history.data]);

  const chart = React.useMemo(() => {
    if (series.length === 0) {
      return null;
    }

    const values = series.map((point) => point.value);
    const maxValue = Math.max(...values);
    const minValue = Math.min(...values);
    const span = maxValue - minValue;

    const xAt = (index: number) =>
      series.length === 1
        ? PAD_LEFT + INNER_WIDTH / 2
        : PAD_LEFT + (index / (series.length - 1)) * INNER_WIDTH;

    const yAt = (value: number) =>
      span === 0
        ? PAD_TOP + INNER_HEIGHT / 2
        : PAD_TOP + INNER_HEIGHT - ((value - minValue) / span) * INNER_HEIGHT;

    const coords = series.map((point, index) => ({
      ...point,
      x: xAt(index),
      y: yAt(point.value),
    }));

    const linePath = coords
      .map(
        (point, index) =>
          `${index === 0 ? 'M' : 'L'} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`,
      )
      .join(' ');

    const first = coords[0];
    const last = coords[coords.length - 1];
    const areaPath =
      coords.length > 1
        ? `${linePath} L ${last.x.toFixed(2)} ${BASELINE} L ${first.x.toFixed(2)} ${BASELINE} Z`
        : null;

    const ticks =
      span === 0 ? [minValue] : [maxValue, minValue + span / 2, minValue];

    return { coords, linePath, areaPath, ticks, yAt, maxValue, minValue };
  }, [series]);

  const periodSwitcher = (
    <div className="flex gap-2">
      {PERIODS.map((period) => (
        <button
          key={period}
          type="button"
          onClick={() => setDays(period)}
          className={cn('btn-sm', days === period ? 'btn-primary' : 'btn-secondary')}
        >
          {period} {plural(period, 'день', 'дня', 'дней')}
        </button>
      ))}
    </div>
  );

  let body: React.ReactNode;

  if (history.isLoading) {
    body = (
      <div className="h-[200px] rounded-[24px] border border-border-light bg-ivory-elevated animate-pulse" />
    );
  } else if (history.isError) {
    body = (
      <div className="rounded-[24px] border border-border-light bg-ivory-elevated p-6">
        <div className="text-[15px] text-clay mb-3">
          {apiErrorMessage(history.error, 'Не удалось загрузить историю цен')}
        </div>
        <button type="button" onClick={() => history.refetch()} className="btn-secondary btn-sm">
          Повторить
        </button>
      </div>
    );
  } else if (!chart) {
    body = (
      <EmptyState text="Данных пока недостаточно: за выбранный период мы ещё не собрали историю цен по этому товару." />
    );
  } else {
    body = (
      <div className="rounded-[24px] border border-border-light bg-ivory-elevated p-4">
        <svg
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          className="w-full h-auto"
          role="img"
          aria-label={`График минимальной цены за ${days} дней`}
        >
          {chart.ticks.map((tick, index) => {
            const y = chart.yAt(tick);
            return (
              <g key={`${tick}-${index}`}>
                <line
                  x1={PAD_LEFT}
                  y1={y}
                  x2={WIDTH - PAD_RIGHT}
                  y2={y}
                  className="stroke-border-light"
                  strokeWidth="1"
                />
                <text
                  x={PAD_LEFT - 10}
                  y={y + 4}
                  textAnchor="end"
                  className="fill-body-muted"
                  fontSize="12"
                >
                  {formatMoneyValue(Math.round(tick))}
                </text>
              </g>
            );
          })}

          {chart.areaPath && <path d={chart.areaPath} className="fill-slate" opacity="0.08" />}

          <path
            d={chart.linePath}
            fill="none"
            className="stroke-slate"
            strokeWidth="2"
            strokeLinejoin="round"
            strokeLinecap="round"
          />

          {chart.coords.length <= 60 &&
            chart.coords.map((point) => (
              <circle key={point.day} cx={point.x} cy={point.y} r="3" className="fill-slate">
                <title>
                  {`${formatDayShort(point.day)} — ${formatMoneyValue(point.value)} · ${formatNumber(
                    point.stores,
                  )} ${plural(point.stores, 'магазин', 'магазина', 'магазинов')}`}
                </title>
              </circle>
            ))}

          <text
            x={PAD_LEFT}
            y={HEIGHT - 8}
            textAnchor="start"
            className="fill-body-muted"
            fontSize="12"
          >
            {formatDayShort(chart.coords[0].day)}
          </text>

          {chart.coords.length > 1 && (
            <text
              x={WIDTH - PAD_RIGHT}
              y={HEIGHT - 8}
              textAnchor="end"
              className="fill-body-muted"
              fontSize="12"
            >
              {formatDayShort(chart.coords[chart.coords.length - 1].day)}
            </text>
          )}
        </svg>

        <div className="flex justify-between text-[13px] text-body-subtle mt-3 flex-wrap gap-2">
          <span>
            Минимум за период:{' '}
            <strong className="text-slate">{formatMoneyValue(chart.minValue)}</strong>
          </span>
          <span>
            Максимум за период:{' '}
            <strong className="text-slate">{formatMoneyValue(chart.maxValue)}</strong>
          </span>
        </div>
      </div>
    );
  }

  return (
    <section className="mb-10">
      <div className="flex justify-between items-end gap-4 mb-4 flex-wrap">
        <div>
          <h2 className="text-[24px] font-semibold text-slate mb-1">История цены</h2>
          <p className="text-[15px] text-body-subtle">
            Минимальная цена по городу за выбранный период
          </p>
        </div>
        {periodSwitcher}
      </div>

      {body}
    </section>
  );
}
