'use strict';

// Proxy-aware HTTPS client with zero dependencies.
//
// Node's global fetch (undici) ignores HTTPS_PROXY, and this environment routes
// all outbound HTTPS through a CONNECT proxy with a re-terminated TLS chain.
// So we tunnel manually and trust the CA bundle the environment provides.

const http = require('node:http');
const https = require('node:https');
const tls = require('node:tls');
const fs = require('node:fs');

const CA_FILE = process.env.NODE_EXTRA_CA_CERTS || process.env.SSL_CERT_FILE;

let CA = null;
try {
  if (CA_FILE && fs.existsSync(CA_FILE)) CA = fs.readFileSync(CA_FILE);
} catch {
  CA = null;
}

function proxyFor(target) {
  const raw = process.env.HTTPS_PROXY || process.env.https_proxy;
  if (!raw) return null;

  const host = target.hostname.toLowerCase();
  const noProxy = (process.env.NO_PROXY || process.env.no_proxy || '')
    .split(',')
    .map((s) => s.trim().toLowerCase())
    .filter(Boolean);

  for (const entry of noProxy) {
    const bare = entry.replace(/^\*?\./, '');
    if (!bare) continue;
    if (host === bare || host.endsWith('.' + bare)) return null;
  }

  return new URL(raw);
}

function connectThroughProxy(proxy, target) {
  return new Promise((resolve, reject) => {
    const port = Number(target.port) || 443;
    const authority = `${target.hostname}:${port}`;
    const headers = { Host: authority };

    if (proxy.username) {
      const creds = `${decodeURIComponent(proxy.username)}:${decodeURIComponent(proxy.password || '')}`;
      headers['Proxy-Authorization'] = 'Basic ' + Buffer.from(creds).toString('base64');
    }

    const req = http.request({
      host: proxy.hostname,
      port: Number(proxy.port) || 80,
      method: 'CONNECT',
      path: authority,
      headers,
    });

    req.once('connect', (res, socket) => {
      if (res.statusCode !== 200) {
        socket.destroy();
        reject(new Error(`proxy CONNECT to ${authority} failed with ${res.statusCode}`));
        return;
      }
      resolve(socket);
    });
    req.once('error', reject);
    req.end();
  });
}

/**
 * Perform an HTTPS request, tunnelling through the agent proxy when one is set.
 * Returns { status, headers, text, json }. Never throws on non-2xx — callers
 * decide what a status means.
 */
async function request(urlStr, options = {}) {
  const { method = 'GET', headers = {}, body = null, timeoutMs = 180000 } = options;
  const target = new URL(urlStr);
  const proxy = proxyFor(target);

  const opts = {
    method,
    host: target.hostname,
    port: Number(target.port) || 443,
    path: target.pathname + target.search,
    headers: { ...headers },
    servername: target.hostname,
  };
  if (CA) opts.ca = CA;

  if (proxy) {
    const socket = await connectThroughProxy(proxy, target);
    opts.agent = false;
    opts.createConnection = () =>
      tls.connect({ socket, servername: target.hostname, ...(CA ? { ca: CA } : {}) });
  }

  return new Promise((resolve, reject) => {
    const req = https.request(opts, (res) => {
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => {
        const text = Buffer.concat(chunks).toString('utf8');
        let json = null;
        try {
          json = JSON.parse(text);
        } catch {
          json = null;
        }
        resolve({ status: res.statusCode, headers: res.headers, text, json });
      });
    });

    req.setTimeout(timeoutMs, () => {
      req.destroy(new Error(`request to ${target.hostname} timed out after ${timeoutMs}ms`));
    });
    req.on('error', reject);

    if (body != null) req.write(typeof body === 'string' ? body : JSON.stringify(body));
    req.end();
  });
}

module.exports = { request, proxyFor, caFile: CA_FILE, hasCa: Boolean(CA) };
