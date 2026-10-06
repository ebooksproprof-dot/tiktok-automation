import { getValidTokenBundle, json, requireDemoSession, tiktokPost } from "./_shared.mjs";

export default async function handler(req) {
  try {
    if (!(await requireDemoSession(req))) return json({ error: "Sessão não autorizada. Conecte o TikTok novamente." }, 401);
    const url = new URL(req.url);
    const publishId = (url.searchParams.get("publish_id") || "").trim();
    if (!publishId) return json({ error: "publish_id é obrigatório." }, 400);

    const bundle = await getValidTokenBundle();
    const result = await tiktokPost("/v2/post/publish/status/fetch/", bundle.access_token, { publish_id: publishId });
    const d = result.data || {};
    return json({
      status: d.status || "UNKNOWN",
      fail_reason: d.fail_reason || "",
      publicly_available_post_id: d.publicly_available_post_id || d.publicaly_available_post_id || "",
    });
  } catch (error) {
    return json({ error: String(error.message || error) }, error.status || 500);
  }
}
