'use strict';

// Provider registry. Both xAI and OpenAI expose an OpenAI-compatible
// /v1/chat/completions endpoint, so one code path serves both.
//
// Model IDs are NOT hardcoded as the single source of truth: an explicit
// --model flag wins, then the env override, then the first entry of `prefer`
// that the provider's own /v1/models actually reports. That way the setup does
// not rot when vendors rename or retire models.

const PROVIDERS = {
  grok: {
    id: 'grok',
    label: 'Grok (xAI)',
    baseUrl: process.env.XAI_BASE_URL || 'https://api.x.ai/v1',
    keyEnv: ['XAI_API_KEY', 'GROK_API_KEY'],
    modelEnv: 'XAI_MODEL',
    prefer: [
      'grok-4',
      'grok-4-latest',
      'grok-4-fast-reasoning',
      'grok-code-fast-1',
      'grok-3',
      'grok-3-latest',
      'grok-2-latest',
    ],
    consoleUrl: 'https://console.x.ai',
  },
  codex: {
    id: 'codex',
    label: 'Codex (OpenAI)',
    baseUrl: process.env.OPENAI_BASE_URL || 'https://api.openai.com/v1',
    keyEnv: ['OPENAI_API_KEY'],
    modelEnv: 'OPENAI_MODEL',
    prefer: [
      'gpt-5.1-codex',
      'gpt-5-codex',
      'gpt-5.1',
      'gpt-5',
      'o4-mini',
      'gpt-4.1',
      'gpt-4o',
    ],
    consoleUrl: 'https://platform.openai.com/api-keys',
  },
};

function get(name) {
  const p = PROVIDERS[String(name || '').toLowerCase()];
  if (!p) {
    throw new Error(`unknown provider "${name}" (known: ${Object.keys(PROVIDERS).join(', ')})`);
  }
  return p;
}

function apiKey(provider) {
  for (const name of provider.keyEnv) {
    const v = process.env[name];
    if (v && v.trim()) return v.trim();
  }
  return null;
}

module.exports = { PROVIDERS, get, apiKey, names: () => Object.keys(PROVIDERS) };
