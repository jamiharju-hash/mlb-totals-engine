import test from 'node:test';
import assert from 'node:assert/strict';
import { renderToStaticMarkup } from 'react-dom/server';
import { DataState } from './DataState';

test('renders DataState loading', () => {
  const html = renderToStaticMarkup(<DataState state="loading" />);
  assert.match(html, /loading-skeleton/);
});


test('prioritizes state UI over children when state is provided', () => {
  const html = renderToStaticMarkup(
    <DataState state="loading">
      <div>ready</div>
    </DataState>
  );

  assert.match(html, /loading-skeleton/);
  assert.doesNotMatch(html, /ready/);
});

test('renders empty, error, and children', () => {
  assert.match(renderToStaticMarkup(<DataState state="empty" message="No picks" />), /No picks/);
  assert.match(renderToStaticMarkup(<DataState state="error" />), /NEXT_PUBLIC_SUPABASE_URL/);
  assert.match(renderToStaticMarkup(<DataState><div>ready</div></DataState>), /ready/);
});
