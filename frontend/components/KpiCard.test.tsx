import test from 'node:test';
import assert from 'node:assert/strict';
import { renderToStaticMarkup } from 'react-dom/server';
import { KpiCard } from './KpiCard';

test('renders KpiCard', () => {
  const html = renderToStaticMarkup(<KpiCard label="ROI" value="12%" />);
  assert.match(html, /ROI/);
  assert.match(html, /12%/);
});

test('handles alert and trend variants', () => {
  assert.match(renderToStaticMarkup(<KpiCard label="ROI" value="-3%" alert />), /text-rose-400/);
  assert.match(renderToStaticMarkup(<KpiCard label="ROI" value="12%" trend="up" />), /trend-up/);
  assert.match(renderToStaticMarkup(<KpiCard label="ROI" value="12%" trend="down" />), /trend-down/);
  assert.match(renderToStaticMarkup(<KpiCard label="ROI" value="12%" trend="neutral" sub="last 7d" />), /last 7d/);
});
