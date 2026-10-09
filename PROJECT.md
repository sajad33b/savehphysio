# پروژه savehphysio.ir — راهنمای کار با Grok / توسعه

سایت کلینیک فیزیوتراپی ابن‌سینا ساوه روی GitHub Pages.

## معماری (مهم)

محتوا و سئو از قالب جدا هستند:

| نقش | مسیر |
|-----|------|
| محتوا + سئو صفحه اول | `content/home.json` |
| قالب ظاهر و ساختار HTML | `templates/home.html` |
| اسکریپت ساخت خروجی | `scripts/build_home.py` |
| صفحه نهایی که روی سایت می‌آید | `index.html` |
| استایل | `styles.css` |
| نسخه AMP | `amp.html` |

```
content/home.json  +  templates/home.html
        ↓
  python3 scripts/build_home.py
        ↓
     index.html   ← همان چیزی که کاربر و گوگل می‌بینند
```

## «Build» یعنی چه؟

Build یعنی **یک‌بار اجرای اسکریپت** تا از روی JSON و قالب، فایل `index.html` دوباره ساخته شود.

- شما متن را در `home.json` عوض می‌کنید
- قالب را در `templates/home.html` عوض می‌کنید
- با build این دو قاطی می‌شوند و `index.html` به‌روز می‌شود

بدون build، تغییر JSON به‌تنهایی روی سایت دیده نمی‌شود.

دستور:

```bash
python3 scripts/build_home.py
```

از ریشهٔ ریپو اجرا شود.

## قوانین کار (برای انسان و AI)

1. **تغییر متن یا سئو** → فقط `content/home.json` → بعد build → commit
2. **تغییر ظاهر/چیدمان** → `templates/home.html` و در صورت نیاز `styles.css` → بعد build → commit
3. **`index.html` را دستی منبع حقیقت ندانید**؛ خروجی build است
4. دامنه: `https://savehphysio.ir/` — ریپو: `sajad33b/savehphysio` — شاخه: `main`

## هدف‌های بعدی (برنامه)

- پنل ادمین روی همین `home.json`
- بعداً مهاجرت محتوا/سئو به هاست وردپرس با همان فیلدهای JSON

## ارجاع در چت جدید با Grok

کافی است بگویید:

> طبق `PROJECT.md` روی savehphysio کار کن.

یا:

> متن را در content/home.json عوض کن و build بگیر.
