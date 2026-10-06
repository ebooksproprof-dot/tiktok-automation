import {
  createDemoSession,
  demoSessionCookie,
  exchangeCode,
  htmlPage,
  parseCookies,
  tokenStore,
  TOKEN_KEY,
} from "./_shared.mjs";

const clearState = "tiktok_oauth_state=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0";

export default async function handler(req) {
  try {
    const url = new URL(req.url);
    const q = url.searchParams;

    if (q.get("error")) {
      return new Response(
        htmlPage("Autorização não concluída", q.get("error_description") || q.get("error"), false),
        {
          status: 400,
          headers: {
            "Content-Type": "text/html; charset=utf-8",
            "Cache-Control": "no-store",
            "Set-Cookie": clearState,
          },
        },
      );
    }

    const code = (q.get("code") || "").trim();
    const returnedState = (q.get("state") || "").trim();
    const cookies = parseCookies(req.headers.get("cookie") || "");
    const expectedState = cookies.tiktok_oauth_state || "";

    if (!code) throw new Error("TikTok não retornou o código de autorização.");
    if (!returnedState || !expectedState || returnedState !== expectedState) {
      throw new Error("Falha na validação de segurança (state). Inicie o login novamente.");
    }

    const token = await exchangeCode(code);
    const now = Date.now();
    const bundle = {
      access_token: token.access_token,
      refresh_token: token.refresh_token,
      open_id: token.open_id,
      scope: token.scope,
      token_type: token.token_type,
      expires_in: Number(token.expires_in || 0),
      refresh_expires_in: Number(token.refresh_expires_in || 0),
      expires_at: now + Number(token.expires_in || 0) * 1000,
      refresh_expires_at: now + Number(token.refresh_expires_in || 0) * 1000,
      updated_at: new Date(now).toISOString(),
    };

    await tokenStore().setJSON(TOKEN_KEY, bundle);
    const sessionId = await createDemoSession();

    const headers = new Headers({
      Location: "/demo.html?connected=1",
      "Cache-Control": "no-store",
    });
    headers.append("Set-Cookie", clearState);
    headers.append("Set-Cookie", demoSessionCookie(sessionId));

    return new Response("", { status: 302, headers });
  } catch (error) {
    return new Response(
      htmlPage("Não foi possível conectar", String(error.message || error), false),
      {
        status: 400,
        headers: {
          "Content-Type": "text/html; charset=utf-8",
          "Cache-Control": "no-store",
          "Set-Cookie": clearState,
        },
      },
    );
  }
}
