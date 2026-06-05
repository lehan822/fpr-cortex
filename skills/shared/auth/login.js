#!/usr/bin/env node
/**
 * fpr-cortex auth login — PKCE OAuth flow via Traveloka Cognito
 * 
 * Usage:
 *   node login.js              # default: staging
 *   node login.js --env prod   # production
 *   node login.js --env stg    # staging (explicit)
 *
 * Opens browser → user logs in via SSO → token saved to ~/.fpr/auth.json
 * Zero dependencies (Node.js built-in only).
 */

const http = require('http');
const https = require('https');
const crypto = require('crypto');
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const url = require('url');

// --- Environment Config ---
const ENVS = {
  stg: {
    name: 'staging',
    authorizeUrl: 'https://internal-id.ath.staging-traveloka.com/oauth2/authorize',
    tokenUrl: 'https://internal-id.ath.staging-traveloka.com/oauth2/token',
    clientId: '38taf824vlbfba3lta3eitcuhi',
  },
  prod: {
    name: 'production',
    authorizeUrl: 'https://internal-id.ath.traveloka.com/oauth2/authorize',
    tokenUrl: 'https://internal-id.ath.traveloka.com/oauth2/token',
    clientId: 'i01t804ups4dme8p1kfoat8jb',
  },
};

// Parse args
const args = process.argv.slice(2);
const envArg = args.includes('--env') ? args[args.indexOf('--env') + 1] : 'stg';
const envKey = envArg === 'production' || envArg === 'prod' ? 'prod' : 'stg';
const config = ENVS[envKey];

const PORT = 18765;
const REDIRECT_URI = `http://localhost:${PORT}/callback`;
const AUTH_DIR = path.join(process.env.HOME, '.fpr');
const AUTH_FILE = path.join(AUTH_DIR, 'auth.json');

// --- PKCE helpers ---
function base64url(buf) {
  return buf.toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}

function generatePKCE() {
  const verifier = base64url(crypto.randomBytes(32));
  const challenge = base64url(crypto.createHash('sha256').update(verifier).digest());
  return { verifier, challenge };
}

function openBrowser(url) {
  const cmd = process.platform === 'darwin' ? 'open' :
              process.platform === 'win32' ? 'start' : 'xdg-open';
  exec(`${cmd} "${url}"`);
}

// --- Token exchange ---
function exchangeCode(code, verifier) {
  return new Promise((resolve, reject) => {
    const body = new URLSearchParams({
      grant_type: 'authorization_code',
      client_id: config.clientId,
      code,
      redirect_uri: REDIRECT_URI,
      code_verifier: verifier,
    }).toString();

    const parsed = new URL(config.tokenUrl);
    const options = {
      hostname: parsed.hostname,
      path: parsed.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': Buffer.byteLength(body),
      },
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        if (res.statusCode !== 200) {
          reject(new Error(`Token exchange failed (${res.statusCode}): ${data}`));
        } else {
          resolve(JSON.parse(data));
        }
      });
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

// --- Main ---
async function main() {
  const { verifier, challenge } = generatePKCE();
  const state = base64url(crypto.randomBytes(16));

  const authUrl = `${config.authorizeUrl}?` + new URLSearchParams({
    response_type: 'code',
    client_id: config.clientId,
    redirect_uri: REDIRECT_URI,
    scope: 'openid email profile',
    state,
    code_challenge: challenge,
    code_challenge_method: 'S256',
  }).toString();

  // Start callback server
  const server = http.createServer(async (req, res) => {
    const parsed = url.parse(req.url, true);
    if (parsed.pathname !== '/callback') {
      res.writeHead(404);
      res.end('Not found');
      return;
    }

    const { code, state: returnedState, error } = parsed.query;

    if (error) {
      res.writeHead(400);
      res.end(`<html><body><h2>❌ Login failed: ${error}</h2></body></html>`);
      console.error(`❌ Login failed: ${error}`);
      process.exit(1);
    }

    if (returnedState !== state) {
      res.writeHead(400);
      res.end('<html><body><h2>❌ State mismatch</h2></body></html>');
      console.error('❌ State mismatch');
      process.exit(1);
    }

    try {
      const tokens = await exchangeCode(code, verifier);

      // Save tokens
      fs.mkdirSync(AUTH_DIR, { recursive: true });
      const authData = {
        env: envKey,
        environment: config.name,
        id_token: tokens.id_token,
        access_token: tokens.access_token,
        refresh_token: tokens.refresh_token,
        expires_at: Date.now() + (tokens.expires_in * 1000),
        obtained_at: new Date().toISOString(),
      };
      fs.writeFileSync(AUTH_FILE, JSON.stringify(authData, null, 2));

      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end(`<html><body style="font-family:sans-serif;text-align:center;padding:60px">
        <h2>✅ Login successful!</h2>
        <p>Environment: <b>${config.name}</b></p>
        <p>Token saved to ~/.fpr/auth.json</p>
        <p style="color:#888">You can close this tab.</p>
      </body></html>`);

      console.log(`✅ Login successful (${config.name})`);
      console.log(`   Token saved to ${AUTH_FILE}`);
      server.close(() => process.exit(0));
    } catch (err) {
      res.writeHead(500);
      res.end(`<html><body><h2>❌ ${err.message}</h2></body></html>`);
      console.error(`❌ ${err.message}`);
      process.exit(1);
    }
  });

  server.listen(PORT, () => {
    console.log(`\n🔐 FPR Login (${config.name})`);
    console.log(`   Opening browser...\n`);
    console.log(`   If browser doesn't open, visit:`);
    console.log(`   ${authUrl}\n`);
    openBrowser(authUrl);
  });

  // Timeout after 120s
  setTimeout(() => {
    console.error('\n⏰ Login timed out (120s). Try again.');
    server.close(() => process.exit(1));
  }, 120_000);
}

main();
