const apiBase = process.env.SMOKE_API_BASE || process.env.VITE_API_BASE || 'http://127.0.0.1:8000/api/v1';

async function assertOk(response, label) {
  if (!response.ok) {
    const body = await response.text().catch(() => '');
    throw new Error(`${label} failed: ${response.status} ${response.statusText} ${body.slice(0, 300)}`);
  }
  return response;
}

async function smokePersonas() {
  const response = await assertOk(await fetch(`${apiBase}/personas`), 'GET /personas');
  const personas = await response.json();
  if (!Array.isArray(personas) || !personas.some((persona) => persona.id === 'customer')) {
    throw new Error('GET /personas did not return the customer persona');
  }
  console.log(`GET /personas ok (${personas.length} personas)`);
}

async function smokeChat() {
  const response = await assertOk(
    await fetch(`${apiBase}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: 'Xin chao',
        display_query: 'Xin chao',
        persona: 'customer',
        deep_search: false,
      }),
    }),
    'POST /chat'
  );

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('POST /chat did not return a readable SSE body');
  }

  const decoder = new TextDecoder();
  let payload = '';
  for (let index = 0; index < 8; index += 1) {
    const { value, done } = await reader.read();
    if (done) break;
    payload += decoder.decode(value, { stream: true });
    if (payload.includes('conversation_id') || payload.includes('[DONE]')) break;
  }
  await reader.cancel().catch(() => {});

  if (!payload.includes('data:')) {
    throw new Error('POST /chat did not stream SSE data');
  }
  console.log('POST /chat ok (SSE started)');
}

await smokePersonas();
await smokeChat();
console.log(`API v1 smoke passed: ${apiBase}`);
