import { getValidTokenBundle, json, requireDemoSession, tiktokPost } from "./_shared.mjs";

export default async function handler(req) {
  try {
    if (req.method !== "POST") return json({ error: "Método não permitido." }, 405);
    if (!(await requireDemoSession(req))) return json({ error: "Sessão não autorizada. Conecte o TikTok novamente." }, 401);

    const body = await req.json();
    if (body?.consent !== true) return json({ error: "É necessária confirmação explícita antes da publicação." }, 400);

    const videoUrl = String(body.video_url || "").trim();
    const title = String(body.title || "").trim().slice(0, 150);
    const privacy = String(body.privacy_level || "").trim();

    if (!videoUrl.startsWith("https://")) return json({ error: "A URL do vídeo deve usar HTTPS." }, 400);
    if (!privacy) return json({ error: "Escolha a privacidade da publicação." }, 400);

    const bundle = await getValidTokenBundle();
    const creator = await tiktokPost("/v2/post/publish/creator_info/query/", bundle.access_token, {});
    const options = creator.data?.privacy_level_options || [];
    if (!options.includes(privacy)) {
      return json({ error: "A opção de privacidade não está disponível para esta conta." }, 400);
    }

    const result = await tiktokPost("/v2/post/publish/video/init/", bundle.access_token, {
      post_info: {
        title,
        privacy_level: privacy,
        disable_duet: !!body.disable_duet,
        disable_comment: !!body.disable_comment,
        disable_stitch: !!body.disable_stitch,
      },
      source_info: {
        source: "PULL_FROM_URL",
        video_url: videoUrl,
      },
    });

    const publishId = result.data?.publish_id;
    if (!publishId) throw new Error("TikTok não retornou publish_id.");

    return json({ ok: true, publish_id: publishId, status: "PROCESSING_DOWNLOAD" }, 202);
  } catch (error) {
    return json({ error: String(error.message || error) }, error.status || 500);
  }
}
