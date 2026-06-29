export const parseFoodInlineParts = (text, { showPartialLoading = false } = {}) => {
  const parts = [];
  const completeMarker = /\[\[FOOD_CARD\s+({[\s\S]*?})\]\]/g;
  let cursor = 0;
  let match;

  while ((match = completeMarker.exec(text)) !== null) {
    const before = text.slice(cursor, match.index);
    if (before) parts.push({ type: 'text', text: before });
    try {
      const parsed = JSON.parse(match[1]);
      if (parsed && typeof parsed === 'object') {
        parts.push({ type: 'food_card', card: parsed });
      }
    } catch (error) {
      console.error('FOOD_CARD marker parse error:', error);
      parts.push({ type: 'text', text: match[0] });
    }
    cursor = completeMarker.lastIndex;
  }

  const tail = text.slice(cursor);
  const partialStart = tail.lastIndexOf('[[FOOD_CARD');

  
  const partials = [
    '[[F', '[[FO', '[[FOO', '[[FOOD', '[[FOOD_',
    '[[FOOD_C', '[[FOOD_CA', '[[FOOD_CAR', '[[FOOD_CARD'
  ];
  let tailMatchIndex = -1;
  for (const p of partials) {
    if (tail.endsWith(p)) {
      tailMatchIndex = tail.length - p.length;
      break;
    }
  }

  const hasPartialMarker = (partialStart !== -1 && tail.indexOf(']]', partialStart) === -1) || tailMatchIndex !== -1;

  if (showPartialLoading && hasPartialMarker) {
    const cutoff = partialStart !== -1 ? partialStart : tailMatchIndex;
    const visibleTail = tail.slice(0, cutoff);
    if (visibleTail) parts.push({ type: 'text', text: visibleTail });
    parts.push({ type: 'food_loading' });
  } else if (tail) {
    parts.push({ type: 'text', text: tail });
  }

  return parts;
};

export const foodInlineText = (parts) => (
  (parts || [])
    .filter((part) => part.type === 'text')
    .map((part) => part.text)
    .join('')
);

export const foodInlineRecommendations = (parts, query, traceId) => {
  const items = (parts || [])
    .filter((part) => part.type === 'food_card')
    .map((part) => part.card);
  return items.length ? { query, trace_id: traceId, items, more_items: [] } : null;
};
