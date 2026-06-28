export const parseRagInlineParts = (text) => {
  const parts = [];
  const completeMarker = /\[\[RAG_CARD\s+({[\s\S]*?})\]\]/g;
  let cursor = 0;
  let match;

  while ((match = completeMarker.exec(text || '')) !== null) {
    const before = text.slice(cursor, match.index);
    if (before) parts.push({ type: 'text', text: before });
    try {
      const parsed = JSON.parse(match[1]);
      if (parsed && typeof parsed === 'object') {
        parts.push({ type: 'rag_card', card: parsed });
      }
    } catch (error) {
      console.error('RAG_CARD marker parse error:', error);
      parts.push({ type: 'text', text: match[0] });
    }
    cursor = completeMarker.lastIndex;
  }

  const tail = (text || '').slice(cursor);
  const partialStart = tail.lastIndexOf('[[RAG_CARD');
  const partials = [
    '[', '[[', '[[R', '[[RA', '[[RAG', '[[RAG_',
    '[[RAG_C', '[[RAG_CA', '[[RAG_CAR', '[[RAG_CARD'
  ];
  let tailMatchIndex = -1;
  for (const partial of partials) {
    if (tail.endsWith(partial)) {
      tailMatchIndex = tail.length - partial.length;
      break;
    }
  }

  if ((partialStart !== -1 && tail.indexOf(']]', partialStart) === -1) || tailMatchIndex !== -1) {
    const cutoff = partialStart !== -1 ? partialStart : tailMatchIndex;
    const visibleTail = tail.slice(0, cutoff);
    if (visibleTail) parts.push({ type: 'text', text: visibleTail });
    parts.push({ type: 'rag_loading' });
  } else if (tail) {
    parts.push({ type: 'text', text: tail });
  }

  return parts;
};

export const ragInlineText = (parts) => (
  (parts || [])
    .filter((part) => part.type === 'text')
    .map((part) => part.text)
    .join('')
);

export const ragInlineCards = (parts) => (
  (parts || [])
    .filter((part) => part.type === 'rag_card')
    .map((part) => part.card)
);

export const ragInlineLoading = (parts) => (
  (parts || []).some((part) => part.type === 'rag_loading')
);
