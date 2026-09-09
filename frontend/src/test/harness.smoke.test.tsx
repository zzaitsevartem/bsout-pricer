import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

function Hello({ name }: { name: string }) {
  return <p>Привет, {name}!</p>;
}

describe('component harness', () => {
  it('renders into jsdom and asserts with jest-dom matchers', () => {
    render(<Hello name="Мир" />);
    expect(screen.getByText('Привет, Мир!')).toBeInTheDocument();
  });
});
