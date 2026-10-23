import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const createMutate = vi.fn();
const launchMutate = vi.fn();

vi.mock('@/models/admin', () => ({
  usePreviewBroadcast: () => ({ mutate: vi.fn(), data: null, isPending: false }),
  useCreateBroadcast: () => ({ mutate: createMutate, isPending: false }),
  useLaunchBroadcast: () => ({ mutate: launchMutate, isPending: false }),
  useBroadcasts: () => ({ data: null }),
  useBroadcastRecipients: () => ({ data: null }),
  useCancelBroadcast: () => ({ mutate: vi.fn() }),
  useDeleteBroadcast: () => ({ mutate: vi.fn() }),
  useSendBroadcastTest: () => ({ mutate: vi.fn() }),
}));

vi.mock('@/models/user', () => ({
  useMe: () => ({ data: null }),
}));

import { BroadcastFormModal } from './MailingsSection';

async function fillForm(user: ReturnType<typeof userEvent.setup>) {
  render(<BroadcastFormModal onClose={() => {}} />);
  await user.type(screen.getByLabelText('Название'), 'Test');
  await user.type(screen.getByLabelText('Адреса получателей'), 'a@b.com');
  await user.type(screen.getByLabelText('Тема письма'), 'Subject');
  await user.type(screen.getByLabelText('Текст письма'), 'Hello');
}

describe('BroadcastFormModal submit mode', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    createMutate.mockImplementation(
      (_payload: unknown, opts?: { onSuccess?: (b: object) => void }) =>
        opts?.onSuccess?.({ id: 7 }),
    );
  });

  it('launches right after create when clicking «Создать и запустить»', async () => {
    const user = userEvent.setup();
    await fillForm(user);

    await user.click(screen.getByRole('button', { name: 'Создать и запустить' }));

    expect(createMutate).toHaveBeenCalledTimes(1);
    expect(launchMutate).toHaveBeenCalledTimes(1);
    expect(launchMutate).toHaveBeenCalledWith(7, expect.anything());
  });

  it('does not launch when clicking «Сохранить черновик»', async () => {
    const user = userEvent.setup();
    await fillForm(user);

    await user.click(screen.getByRole('button', { name: 'Сохранить черновик' }));

    expect(createMutate).toHaveBeenCalledTimes(1);
    expect(launchMutate).not.toHaveBeenCalled();
  });
});
