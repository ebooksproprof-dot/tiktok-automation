import { randomBytes } from "node:crypto";
import { env } from "./_shared.mjs";

export async function handler() {
  try {
    const clientKey = env("TIKTOK_CLIENT_KEY");
    const redirectUri = env("TIKTOK_REDIRECT_URI");
    const scopes = (process.env.TIKTOK_SCOPES || "user.info.basic,video.publish").trim();
    const state = randomBytes(24).toString("hex");

    const auth = new URL("https://www.tiktok.com/v2/auth/authorize/");
    auth.searchParams.set("client_key", clientKey);
    auth.searchParams.set("response_type", "code");
    auth.searchParams.set("scope", scopes);
    auth.searchParams.set("redirect_uri", redirectUri);
    auth.searchParams.set("state", state);

    return {
      statusCode: 302,
      headers: {
        Location: auth.toString(),
        "Cache-Control": "no-store",
        "Set-Cookie": `tiktok_oauth_state=${state}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=600`,
      },
      body: "",
    };
  } catch (error) {
    return { statusCode: 500, headers: { "Cache-Control": "no-store" }, body: String(error.message || error) };
  }
}
