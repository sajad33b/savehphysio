/**
 * savehphysio API worker:
 * - /api/oauth/*  GitHub OAuth (optional)
 * - /api/review   public review submission → content/reviews-pending.json
 *
 * Secrets:
 *   GITHUB_TOKEN          (repo scope) required for reviews
 *   GITHUB_CLIENT_ID      optional oauth
 *   GITHUB_CLIENT_SECRET  optional oauth
 *   OAUTH_STATE_SECRET    optional oauth
 *   ADMIN_ORIGIN          default https://savehphysio.ir
 */

const DEFAULT_ORIGIN = "https://savehphysio.ir";
const REPO = "sajad33b/savehphysio";
const BRANCH = "main";
const PENDING_PATH = "content/reviews-pending.json";

function b64url(buf) {
  const bytes = buf instanceof ArrayBuffer ? new Uint8Array(buf) : buf;
  let s = "";
  for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function toBase64Utf8(str) {
  return btoa(unescape(encodeURIComponent(str)));
}

async function hmacSign(secret, msg) {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(msg));
  return b64url(sig);
}

async function makeState(secret) {
  const nonce = b64url(crypto.getRandomValues(new Uint8Array(16)));
  const ts = String(Math.floor(Date.now() / 1000));
  const payload = `${nonce}.${ts}`;
  const sig = await hmacSign(secret, payload);
  return `${payload}.${sig}`;
}

async function verifyState(secret, state) {
  const parts = (state || "").split(".");
  if (parts.length !== 3) return false;
  const [nonce, ts, sig] = parts;
  const payload = `${nonce}.${ts}`;
  const expect = await hmacSign(secret, payload);
  if (sig !== expect) return false;
  const age = Math.floor(Date.now() / 1000) - parseInt(ts, 10);
  return age >= 0 && age < 600;
}

function htmlPage(title, body) {
  return new Response(
    `<!DOCTYPE html><html lang="fa" dir="rtl"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>${title}</title>
<style>body{font-family:Tahoma,sans-serif;background:#e9ecef;display:flex;min-height:100vh;align-items:center;justify-content:center;margin:0;padding:16px}
.box{background:#fff;border:1px solid #ced4da;border-radius:6px;padding:24px;max-width:420px;width:100%;text-align:center;line-height:1.7}
a{color:#3a6ea5}</style></head><body><div class="box">${body}</div></body></html>`,
    { headers: { "Content-Type": "text/html; charset=utf-8" } }
  );
}

function corsHeaders(origin) {
  return {
    "Access-Control-Allow-Origin": origin || DEFAULT_ORIGIN,
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };
}

function jsonResp(obj, status, origin) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", ...corsHeaders(origin) },
  });
}

async function githubGetFile(token, path) {
  const res = await fetch(
    `https://api.github.com/repos/${REPO}/contents/${path}?ref=${BRANCH}`,
    {
      headers: {
        Accept: "application/vnd.github+json",
        Authorization: `Bearer ${token}`,
        "User-Agent": "savehphysio-worker",
        "X-GitHub-Api-Version": "2022-11-28",
      },
    }
  );
  if (res.status === 404) return { sha: null, json: { pending: [] } };
  if (!res.ok) {
    const t = await res.text();
    throw new Error("github get: " + res.status + " " + t.slice(0, 200));
  }
  const meta = await res.json();
  const text = decodeURIComponent(escape(atob(meta.content.replace(/\n/g, ""))));
  return { sha: meta.sha, json: JSON.parse(text) };
}

async function githubPutFile(token, path, obj, message, sha) {
  const content = JSON.stringify(obj, null, 2) + "\n";
  const body = {
    message,
    content: toBase64Utf8(content),
    branch: BRANCH,
  };
  if (sha) body.sha = sha;
  const res = await fetch(`https://api.github.com/repos/${REPO}/contents/${path}`, {
    method: "PUT",
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      "User-Agent": "savehphysio-worker",
      "X-GitHub-Api-Version": "2022-11-28",
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const t = await res.text();
    throw new Error("github put: " + res.status + " " + t.slice(0, 200));
  }
  return res.json();
}

function cleanText(s, max) {
  return String(s || "")
    .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, "")
    .trim()
    .slice(0, max);
}


async function notifyBale(env, item) {
  const token = env.BALE_BOT_TOKEN;
  const chatId = env.BALE_CHAT_ID;
  if (!token || !chatId) return;
  const stars = "★".repeat(item.rating || 0) + "☆".repeat(5 - (item.rating || 0));
  const text =
    "📝 نظر جدید در سایت\n\n" +
    "نام: " + (item.name || "-") + "\n" +
    "امتیاز: " + stars + "\n" +
    "متن: " + (item.text || "") + "\n" +
    (item.phone ? ("تلفن: " + item.phone + "\n") : "") +
    "شناسه: " + (item.id || "") + "\n\n" +
    "برای تأیید: https://savehphysio.ir/admin/";
  try {
    await fetch("https://tapi.bale.ai/bot" + token + "/sendMessage", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chat_id: chatId, text }),
    });
  } catch (e) {
    // non-fatal
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = env.ADMIN_ORIGIN || DEFAULT_ORIGIN;
    const path = url.pathname;

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders(origin) });
    }

    // ---- Reviews API ----
    if (path === "/api/review" || path.endsWith("/api/review")) {
      if (request.method !== "POST") {
        return jsonResp({ error: "method_not_allowed" }, 405, origin);
      }
      const token = env.GITHUB_TOKEN;
      if (!token) {
        return jsonResp({ error: "server_not_configured" }, 503, origin);
      }
      let body;
      try {
        body = await request.json();
      } catch {
        return jsonResp({ error: "invalid_json" }, 400, origin);
      }
      // honeypot
      if (body.website || body._gotcha) {
        return jsonResp({ ok: true }, 200, origin);
      }
      const name = cleanText(body.name, 80);
      const message = cleanText(body.message || body.text, 1200);
      const phone = cleanText(body.phone, 20);
      let rating = parseInt(body.rating, 10);
      if (!name || !message) {
        return jsonResp({ error: "name_and_message_required" }, 400, origin);
      }
      if (!(rating >= 1 && rating <= 5)) rating = 5;

      const id =
        "r_" +
        Date.now().toString(36) +
        "_" +
        Math.random().toString(36).slice(2, 8);
      const item = {
        id,
        name,
        text: message,
        rating,
        phone: phone || "",
        created: new Date().toISOString().slice(0, 10),
        status: "pending",
      };

      try {
        const file = await githubGetFile(token, PENDING_PATH);
        const data = file.json || { pending: [] };
        if (!Array.isArray(data.pending)) data.pending = [];
        // basic flood protection
        if (data.pending.length > 200) {
          return jsonResp({ error: "queue_full" }, 429, origin);
        }
        data.pending.unshift(item);
        await githubPutFile(
          token,
          PENDING_PATH,
          data,
          "review: new pending " + id,
          file.sha
        );
        await notifyBale(env, item);
        return jsonResp({ ok: true, id }, 200, origin);
      } catch (e) {
        return jsonResp({ error: String(e.message || e) }, 500, origin);
      }
    }

    // ---- OAuth (optional) ----
    const clientId = env.GITHUB_CLIENT_ID;
    const clientSecret = env.GITHUB_CLIENT_SECRET;
    const stateSecret = env.OAUTH_STATE_SECRET || clientSecret || "change-me";

    if (path.endsWith("/oauth/start") || path.endsWith("/api/oauth/start")) {
      if (!clientId || !clientSecret) {
        return htmlPage("پیکربندی ناقص", "<p>OAuth تنظیم نشده است.</p>");
      }
      const state = await makeState(stateSecret);
      const cb = `${url.origin}/api/oauth/callback`;
      const auth = new URL("https://github.com/login/oauth/authorize");
      auth.searchParams.set("client_id", clientId);
      auth.searchParams.set("redirect_uri", cb);
      auth.searchParams.set("scope", "repo");
      auth.searchParams.set("state", state);
      return Response.redirect(auth.toString(), 302);
    }

    if (path.endsWith("/oauth/callback") || path.endsWith("/api/oauth/callback")) {
      if (!clientId || !clientSecret) {
        return htmlPage("خطا", "<p>OAuth تنظیم نشده.</p>");
      }
      const code = url.searchParams.get("code");
      const state = url.searchParams.get("state");
      if (!(await verifyState(stateSecret, state)) || !code) {
        return htmlPage("خطا", `<p>درخواست نامعتبر.</p><p><a href="${origin}/admin/">بازگشت</a></p>`);
      }
      const cb = `${url.origin}/api/oauth/callback`;
      const tokenRes = await fetch("https://github.com/login/oauth/access_token", {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify({
          client_id: clientId,
          client_secret: clientSecret,
          code,
          redirect_uri: cb,
        }),
      });
      const tokenJson = await tokenRes.json();
      if (!tokenJson.access_token) {
        return htmlPage("خطا", `<p>دریافت توکن ناموفق.</p><pre>${JSON.stringify(tokenJson)}</pre>`);
      }
      const userRes = await fetch("https://api.github.com/user", {
        headers: {
          Authorization: `Bearer ${tokenJson.access_token}`,
          Accept: "application/vnd.github+json",
          "User-Agent": "savehphysio-admin",
        },
      });
      const user = await userRes.json();
      const dest = `${origin}/admin/#gh_token=${encodeURIComponent(tokenJson.access_token)}&gh_login=${encodeURIComponent(user.login || "")}`;
      return Response.redirect(dest, 302);
    }

    return jsonResp({ service: "savehphysio-api", endpoints: ["/api/review", "/api/oauth/start"] }, 200, origin);
  },
};
