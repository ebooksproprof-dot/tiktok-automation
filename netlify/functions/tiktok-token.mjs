import { env, refreshBundle, secureEqual, tokenStore, TOKEN_KEY } from "./_shared.mjs";

export default async function handler(req) {
  try {
    const expected = env("RUNNER_SHARED_SECRET");
    const auth = req.headers.get("authorization") || "";
    const supplied = auth.startsWith("Bearer ") ? auth.slice(7).trim() : "";

    if (!secureEqual(supplied, expected)) {
      return new Response(JSON.stringify({ error: "unauthorized" }), {
        status: 401,
        headers: {
          "Content-Type": "application/json",
          "Cache-Control": "no-store",
        },
      });
    }

    const store = tokenStore();
    let bundle = await store.get(TOKEN_KEY, { type: "json", consistency: "strong" });

    if (!bundle?.access_token) {
      return new Response(JSON.stringify({ error: "tiktok_not_connected" }), {
        status: 404,
        headers: {
          "Content-Type": "application/json",
          "Cache-Control": "no-store",
        },
      });
    }

    const refreshMarginMs = 15 * 60 * 1000;
    if (!bundle.expires_at || Number(bundle.expires_at) <= Date.now() + refreshMarginMs) {
      bundle = await refreshBundle(bundle);
      await store.setJSON(TOKEN_KEY, bundle);
    }

    return new Response(JSON.stringify({
      access_token: bundle.access_token,
      expires_at: bundle.expires_at,
      open_id: bundle.open_id,
      scope: bundle.scope,
    }), {
      status: 200,
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
      },
    });
  } catch (error) {
    return new Response(JSON.stringify({
      error: "token_broker_error",
      message: String(error.message || error),
    }), {
      status: 500,
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
      },
    });
  }
}
