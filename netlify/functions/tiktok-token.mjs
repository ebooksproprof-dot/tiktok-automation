import { env, refreshBundle, secureEqual, tokenStore, TOKEN_KEY } from "./_shared.mjs";

export async function handler(event) {
  try {
    const expected = env("RUNNER_SHARED_SECRET");
    const auth = event.headers?.authorization || event.headers?.Authorization || "";
    const supplied = auth.startsWith("Bearer ") ? auth.slice(7).trim() : "";

    if (!secureEqual(supplied, expected)) {
      return { statusCode: 401, headers: { "Cache-Control": "no-store" }, body: JSON.stringify({ error: "unauthorized" }) };
    }

    const store = tokenStore();
    let bundle = await store.get(TOKEN_KEY, { type: "json", consistency: "strong" });
    if (!bundle?.access_token) {
      return { statusCode: 404, headers: { "Cache-Control": "no-store" }, body: JSON.stringify({ error: "tiktok_not_connected" }) };
    }

    const refreshMarginMs = 15 * 60 * 1000;
    if (!bundle.expires_at || Number(bundle.expires_at) <= Date.now() + refreshMarginMs) {
      bundle = await refreshBundle(bundle);
      await store.setJSON(TOKEN_KEY, bundle);
    }

    return {
      statusCode: 200,
      headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
      body: JSON.stringify({
        access_token: bundle.access_token,
        expires_at: bundle.expires_at,
        open_id: bundle.open_id,
        scope: bundle.scope,
      }),
    };
  } catch (error) {
    return {
      statusCode: 500,
      headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
      body: JSON.stringify({ error: "token_broker_error", message: String(error.message || error) }),
    };
  }
}
