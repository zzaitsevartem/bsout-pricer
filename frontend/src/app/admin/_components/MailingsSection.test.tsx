import React, { useState } from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { Modal } from './MailingsSection';

function ControlledForm() {
  const [value, setValue] = useState('');
  const [open, setOpen] = useState(true);
  if (!open) {
    return null;
  }
  return (
    <Modal onClose={() => setOpen(false)}>
      <textarea
        aria-label="emails"
        value={value}
        onChange={(event) => setValue(event.target.value)}
      />
    </Modal>
  );
}

describe('Modal focus', () => {
  it('keeps focus inside the textarea while typing', async () => {
    const user = userEvent.setup();
    render(<ControlledForm />);

    const box = screen.getByLabelText('emails');
    await user.click(box);
    await user.keyboard('user@example.com');

    expect(box).toHaveValue('user@example.com');
    expect(document.activeElement).toBe(box);
  });

  it('closes on Escape', async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(
      <Modal onClose={onClose}>
        <p>hi</p>
      </Modal>,
    );

    await user.keyboard('{Escape}');

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
