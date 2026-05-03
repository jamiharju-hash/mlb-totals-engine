import test from 'node:test';
import assert from 'node:assert/strict';
import { renderToStaticMarkup } from 'react-dom/server';
import { FilterBar, type Filters } from './FilterBar';

const active: Filters = {
  market: ['totals'],
  signal: ['BET_STRONG'],
  team: ['NYY'],
  search: 'yan',
  positiveEdgeOnly: true,
  betSignalsOnly: false,
};

test('renders FilterBar', () => {
  const html = renderToStaticMarkup(
    <FilterBar markets={['totals']} signals={['BET_STRONG']} teams={['NYY']} active={active} onChange={() => {}} />,
  );
  assert.match(html, /Search team or market/);
});

test('renders pills and toggles', () => {
  const html = renderToStaticMarkup(
    <FilterBar markets={['totals', 'moneyline']} signals={['BET_STRONG']} teams={['NYY']} active={active} onChange={() => {}} />,
  );
  assert.match(html, /totals/);
  assert.match(html, /moneyline/);
  assert.match(html, /positive edge only/);
  assert.match(html, /bet signals only/);
});
