import test from 'node:test';
import assert from 'node:assert/strict';
import { renderToStaticMarkup } from 'react-dom/server';
import { SignalBadge } from './SignalBadge';

test('renders SignalBadge', () => {
  const html = renderToStaticMarkup(<SignalBadge signal="BET_STRONG" />);
  assert.match(html, /BET STRONG/);
});

test('renders signal variants with expected classes', () => {
  const strong = renderToStaticMarkup(<SignalBadge signal="BET_STRONG" />);
  const small = renderToStaticMarkup(<SignalBadge signal="BET_SMALL" />);
  const pass = renderToStaticMarkup(<SignalBadge signal="PASS" />);
  const fade = renderToStaticMarkup(<SignalBadge signal="FADE" />);

  assert.match(strong, /text-signal-strong-bet/);
  assert.match(small, /text-signal-small-bet/);
  assert.match(pass, /text-signal-pass/);
  assert.match(fade, /text-signal-fade/);
});
