import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import ErrorPage from './error';

describe('ErrorPage', () => {
  it('shows a 500 heading instead of the default Next error page', () => {
    render(<ErrorPage error={new Error('boom')} reset={vi.fn()} />);

    expect(
      screen.getByRole('heading', { level: 1, name: 'Что-то пошло не так' }),
    ).toBeInTheDocument();
    expect(screen.getByText('Ошибка 500')).toBeInTheDocument();
  });

  it('retries through the reset handler', async () => {
    const user = userEvent.setup();
    const reset = vi.fn();

    render(<ErrorPage error={new Error('boom')} reset={reset} />);
    await user.click(screen.getByRole('button', { name: 'Попробовать снова' }));

    expect(reset).toHaveBeenCalledTimes(1);
  });

  it('survives an error object without a digest', () => {
    render(<ErrorPage error={new Error('boom')} reset={vi.fn()} />);

    expect(screen.queryByText(/Код ошибки/)).not.toBeInTheDocument();
  });

  it('shows the digest so a user can report it', () => {
    const error = Object.assign(new Error('boom'), { digest: 'abc123' });

    render(<ErrorPage error={error} reset={vi.fn()} />);

    expect(screen.getByText('abc123')).toBeInTheDocument();
  });

  it('logs the error for diagnostics', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => null);
    const error = new Error('boom');

    render(<ErrorPage error={error} reset={vi.fn()} />);

    expect(spy).toHaveBeenCalledWith(error);
    spy.mockRestore();
  });
});
