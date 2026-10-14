/**
 * GitHub OAuth proxy for savehphysio admin panel.
 * Secrets (wrangler / dashboard):
 *   GITHUB_CLIENT_ID
 *   GITHUB_CLIENT_SECRET
 *   OAUTH_STATE_SECRET  (random string for state signing)
 * Optional:
 *   ADMIN_ORIGIN = https://savehphysio.ir
 */

const ADMIN_PATH = "/admin/";
const DEFAULT_ORIGIN = "https://savehphysio.ir";

function b64url(buf) {
  const bytes = buf instanceof ArrayBuffer ? new Uint8Array(buf) : buf;
  let s = "";
  for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
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

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = env.ADMIN_ORIGIN || DEFAULT_ORIGIN;
    const clientId = env.GITHUB_CLIENT_ID;
    const clientSecret = env.GITHUB_CLIENT_SECRET;
    const stateSecret = env.OAUTH_STATE_SECRET || clientSecret || "change-me";

    if (!clientId || !clientSecret) {
      return htmlPage(
        "پیکربندی ناقص",
        "<p>Secrets ورکر تنظیم نشده است.</p><p>GITHUB_CLIENT_ID و GITHUB_CLIENT_SECRET را اضافه کنید.</p>"
      );
    }

    // CORS preflight for token handoff API
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": origin,
          "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type",
        },
      });
    }

    // Start OAuth
    if (url.pathname.endsWith("/oauth/start") || url.pathname.endsWith("/api/oauth/start")) {
      const state = await makeState(stateSecret);
      const redirectUri = `${url.origin}${url.pathname.replace(/\/oauth\/start$/, "/oauth/callback").replace(/\/api\/oauth\/start$/, "/api/oauth/callback")}`;
      // Prefer path /api/oauth/callback when under /api
      let cb = `${url.origin}/api/oauth/callback`;
      if (url.pathname.includes("/oauth/") && !url.pathname.includes("/api/")) {
        cb = `${url.origin}/oauth/callback`;
      }
      const auth = new URL("https://github.com/login/oauth/authorize");
      auth.searchParams.set("client_id", clientId);
      auth.searchParams.set("redirect_uri", cb);
      auth.searchParams.set("scope", "repo");
      auth.searchParams.set("state", state);
      return Response.redirect(auth.toString(), 302);
    }

    // Callback from GitHub
    if (url.pathname.endsWith("/oauth/callback") || url.pathname.endsWith("/api/oauth/callback")) {
      const code = url.searchParams.get("code");
      const state = url.searchParams.get("state");
      const err = url.searchParams.get("error");
      if (err) {
        return htmlPage("خطا", `<p>GitHub: ${err}</p><p><a href="${origin}${ADMIN_PATH}">بازگشت به پنل</a></p>`);
      }
      if (!(await verifyState(stateSecret, state))) {
        return htmlPage("خطا", `<p>state نامعتبر یا منقضی است. دوباره تلاش کنید.</p><p><a href="${origin}${ADMIN_PATH}">بازگشت</a></p>`);
      }
      if (!code) {
        return htmlPage("خطا", `<p>کد دریافت نشد.</p><p><a href="${origin}${ADMIN_PATH}">بازگشت</a></p>`);
      }

      let cb = `${url.origin}/api/oauth/callback`;
      if (url.pathname.endsWith("/oauth/callback") && !url.pathname.includes("/api/")) {
        cb = `${url.origin}/oauth/callback`;
      }

      const tokenRes = await fetch("https://github.com/login/oauth/access_token", {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          client_id: clientId,
          client_secret: clientSecret,
          code,
          redirect_uri: cb,
        }),
      });
      const tokenJson = await tokenRes.json();
      if (!tokenJson.access_token) {
        return htmlPage(
          "خطا",
          `<p>دریافت توکن ناموفق بود.</p><pre style="text-align:left;font-size:12px;overflow:auto">${JSON.stringify(tokenJson)}</pre><p><a href="${origin}${ADMIN_PATH}">بازگشت</a></p>`
        );
      }

      // Verify user is repo collaborator / owner by checking API
      const userRes = await fetch("https://api.github.com/user", {
        headers: {
          Authorization: `Bearer ${tokenJson.access_token}`,
          Accept: "application/vnd.github+json",
          "User-Agent": "savehphysio-admin",
        },
      });
      const user = await userRes.json();
      if (!user.login) {
        return htmlPage("خطا", `<p>شناسه کاربر GitHub دریافت نشد.</p><p><a href="${origin}${ADMIN_PATH}">بازگشت</a></p>`);
      }

      // Handoff token to admin via fragment (not sent to server on next requests)
      const dest = `${origin}${ADMIN_PATH}#gh_token=${encodeURIComponent(tokenJson.access_token)}&gh_login=${encodeURIComponent(user.login)}`;
      return Response.redirect(dest, 302);
    }

    return htmlPage(
      "OAuth",
      `<p>ورکر OAuth پنل ادمین savehphysio</p><p><a href="/api/oauth/start">شروع ورود با GitHub</a></p>`
    );
  },
};
