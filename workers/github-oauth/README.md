# GitHub OAuth برای پنل ادمین

این ورکر `client_secret` را روی کلادفلر نگه می‌دارد؛ مرورگر فقط با GitHub وارد می‌شود.

## ۱) ساخت GitHub OAuth App

1. برو به: https://github.com/settings/developers → **OAuth Apps** → **New OAuth App**
2. مقادیر:
   - **Application name:** `savehphysio admin`
   - **Homepage URL:** `https://savehphysio.ir`
   - **Authorization callback URL:** `https://savehphysio.ir/api/oauth/callback`
3. **Register application**
4. **Client ID** را کپی کن
5. **Generate a new client secret** و Secret را کپی کن (فقط یک‌بار نشان داده می‌شود)

## ۲) ساخت Worker در Cloudflare

1. [dash.cloudflare.com](https://dash.cloudflare.com) → Workers & Pages → **Create** → **Create Worker**
2. نام: `savehphysio-oauth`
3. کد داخل `workers/github-oauth/worker.js` را جای کد پیش‌فرض بگذار و **Deploy**
4. **Settings → Variables and Secrets** → Secrets:
   - `GITHUB_CLIENT_ID` = Client ID از گیت‌هاب
   - `GITHUB_CLIENT_SECRET` = Client Secret از گیت‌هاب
   - `OAUTH_STATE_SECRET` = یک رشته تصادفی بلند (مثلاً ۳۰ کاراکتر)
   - (اختیاری) `ADMIN_ORIGIN` = `https://savehphysio.ir`
5. **Settings → Triggers → Routes** → Add route:
   - `savehphysio.ir/api/oauth/*`
   - Zone: savehphysio.ir

## ۳) تست

1. برو به https://savehphysio.ir/admin/
2. **ورود با GitHub** را بزن
3. اجازه دسترسی به ریپو را تأیید کن
4. باید وارد پنل شوی و توکن ذخیره برای ذخیره فایل‌ها تنظیم شود

## امنیت

- `client_secret` فقط در Secrets ورکر است
- توکن با `#` (fragment) به پنل برمی‌گردد و در URL برای سرور ارسال نمی‌شود
- همچنان Cloudflare Access روی `/admin` فعال است
