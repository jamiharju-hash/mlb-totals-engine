import test from 'node:test';
import assert from 'node:assert/strict';
import { renderToStaticMarkup } from 'react-dom/server';
import { StatusBadge } from './StatusBadge';

test('renders StatusBadge', () => {
  const html = renderToStaticMarkup(<StatusBadge status="fresh" />);
  assert.match(html, /fresh/);
});

test('status variants and label override', () => {
  assert.match(renderToStaticMarkup(<StatusBadge status="fresh" />), /bg-emerald-400/);
  assert.match(renderToStaticMarkup(<StatusBadge status="yellow" />), /bg-amber-400/);
  assert.match(renderToStaticMarkup(<StatusBadge status="red" />), /bg-rose-400/);
  assert.match(renderToStaticMarkup(<StatusBadge status="demo" label="staging" />), /staging/);
  assert.match(renderToStaticMarkup(<StatusBadge status="unknown" />), /bg-slate-400/);
});
