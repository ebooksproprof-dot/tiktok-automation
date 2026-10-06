import { getStore } from "@netlify/blobs";
import { randomBytes, timingSafeEqual } from "node:crypto";

export const TOKEN_KEY = "primary";
export const SESSION_COOKIE = "tiktok_demo_session";
const SESSION_TTL_MS = 60 * 60 * 1000;

export function env(name) {
  const value = (process.env[name] || "").trim();
  if (!value) throw new Error(`Missing required environment variable: ${name}`);
  return value;
}

export function tokenStore() {
  return getStore("tiktok-auth");
}

export function demoSessionStore() {
  return getStore("tiktok-demo-sessions");
}

export function parseCookies(raw = "") {
  const out = {};
  for (const part of raw.split(";")) {
    const idx = part.indexOf("=");
    if (idx < 0) continue;
    const key = part.slice(0, idx).trim();
    const value = part.slice(idx + 1).trim();
    if (key) out[key] = decodeURIComponent(value);
  }
  return out;
}

export function secureEqual(a = "", b = "") {
  const ab = Buffer.from(String(a));
  const bb = Buffer.from(String(b));
  return ab.length === bb.length && timingSafeEqual(ab, bb);
}

export async function createDemoSession() {
  const id = randomBytes(32).toString("hex");
  await demoSessionStore().setJSON(id, {
    created_at: new Date().toISOString(),
    expires_at: Date.now() + SESSION_TTL_MS,
  });
  return id;
}

export async function requireDemoSession(req) {
  const cookies = parseCookies(req.headers.get("cookie") || "");
  const id = cookies[SESSION_COOKIE] || "";
  if (!id) return false;
  const session = await demoSessionStore().get(id, { type: "json" });
  if (!session || Number(session.expires_at || 0) < Date.now()) return false;
  return true;
}

export function demoSessionCookie(id) {
  return `${SESSION_COOKIE}=${encodeURIComponent(id)}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=3600`;
}

export function htmlPage(title, message, ok = true) {
  const accent = ok ? "#166534" : "#991b1b";
  return `<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${title}</title></head>
<body style="font-family:system-ui,-apple-system,Segoe UI,sans-serif;background:#f5f7fb;margin:0;padding:32px;color:#172033">
<main style="max-width:680px;margin:8vh auto;background:white;padding:32px;border-radius:18px;border:1px solid #e1e6ef">
<h1 style="margin-top:0;color:${accent}">${title}</h1>
<p style="font-size:18px;line-height:1.6">${message}</p>
<p style="color:#667085">Você pode voltar ao painel e tentar novamente.</p>
</main></body></html>`;
}

export async function exchangeCode(code) {
  const clientKey = env("TIKTOK_CLIENT_KEY");
  const clientSecret = env("TIKTOK_CLIENT_SECRET");
  const redirectUri = env("TIKTOK_REDIRECT_URI");

  const body = new URLSearchParams({
    client_key: clientKey,
    client_secret: clientSecret,
    code,
    grant_type: "authorization_code",
    redirect_uri: redirectUri,
  });

  const response = await fetch("https://open.tiktokapis.com/v2/oauth/token/", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "Cache-Control": "no-cache",
    },
    body,
  });

  const data = await response.json();
  if (!response.ok || data.error) {
    throw new Error(data.error_description || data.error || `TikTok token exchange failed (${response.status})`);
  }
  return data;
}

export async function refreshBundle(bundle) {
  const clientKey = env("TIKTOK_CLIENT_KEY");
  const clientSecret = env("TIKTOK_CLIENT_SECRET");
  if (!bundle?.refresh_token) throw new Error("No refresh token stored");

  const body = new URLSearchParams({
    client_key: clientKey,
    client_secret: clientSecret,
    grant_type: "refresh_token",
    refresh_token: bundle.refresh_token,
  });

  const response = await fetch("https://open.tiktokapis.com/v2/oauth/token/", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "Cache-Control": "no-cache",
    },
    body,
  });

  const data = await response.json();
  if (!response.ok || data.error) {
    throw new Error(data.error_description || data.error || `TikTok token refresh failed (${response.status})`);
  }

  const now = Date.now();
  return {
    ...bundle,
    ...data,
    expires_at: now + Number(data.expires_in || 0) * 1000,
    refresh_expires_at: now + Number(data.refresh_expires_in || 0) * 1000,
    updated_at: new Date(now).toISOString(),
  };
}

export async function getValidTokenBundle() {
  const store = tokenStore();
  let bundle = await store.get(TOKEN_KEY, { type: "json" });
  if (!bundle?.access_token) throw new Error("Nenhuma conta TikTok está conectada.");

  if (Number(bundle.expires_at || 0) < Date.now() + 60_000) {
    bundle = await refreshBundle(bundle);
    await store.setJSON(TOKEN_KEY, bundle);
  }
  return bundle;
}

export async function tiktokPost(path, accessToken, body) {
  const response = await fetch(`https://open.tiktokapis.com${path}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json; charset=UTF-8",
    },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  const error = data?.error || {};
  if (!response.ok || (error.code && error.code !== "ok")) {
    const err = new Error(error.message || error.code || `TikTok request failed (${response.status})`);
    err.status = response.status || 400;
    throw err;
  }
  return data;
}

export function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    },
  });
}
