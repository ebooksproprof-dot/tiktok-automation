import { getValidTokenBundle, json, requireDemoSession, tiktokPost } from "./_shared.mjs";

export default async function handler(req) {
  try {
    if (!(await requireDemoSession(req))) return json({ error: "Sessão não autorizada. Conecte o TikTok novamente." }, 401);
    const bundle = await getValidTokenBundle();
    const result = await tiktokPost("/v2/post/publish/creator_info/query/", bundle.access_token, {});
    const d = result.data || {};
    return json({
      creator_username: d.creator_username || "",
      creator_nickname: d.creator_nickname || "",
      privacy_level_options: d.privacy_level_options || [],
      comment_disabled: !!d.comment_disabled,
      duet_disabled: !!d.duet_disabled,
      stitch_disabled: !!d.stitch_disabled,
      max_video_post_duration_sec: d.max_video_post_duration_sec || null,
    });
  } catch (error) {
    return json({ error: String(error.message || error) }, error.status || 500);
  }
}
