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
| **پنل مدیریت** | `admin/` (Decap CMS) |

```
content/*.json  +  templates/*.html
        ↓
  python3 scripts/build_*.py
        ↓
     *.html   ← همان چیزی که کاربر و گوگل می‌بینند
```

## پنل ادمین (جدید)

- آدرس: https://savehphysio.ir/admin/
- سیستم: Decap CMS (قبلاً Netlify CMS)
- فایل تنظیمات: `admin/config.yml`
- محتوا را مستقیم از روی فایل‌های JSON در پوشه `content/` ویرایش می‌کند
- ظاهر و منوها ساده و خلوت طراحی شده (نزدیک به حس بلاگ بیان)

### مجموعه‌های قابل ویرایش فعلی:
- صفحه اصلی
- درباره ما
- خدمات
- تماس و نوبت
- مقالات وبلاگ

بعد از ذخیره در پنل، تغییرات به صورت commit در گیت‌هاب ثبت می‌شود. سپس باید اسکریپت‌های build را اجرا کرد تا صفحات HTML به‌روز شوند (در نسخه‌های بعدی می‌توان build را خودکار کرد).

## «Build» یعنی چه؟

Build یعنی **یک‌بار اجرای اسکریپت** تا از روی JSON و قالب، فایل HTML دوباره ساخته شود.

دستور نمونه:

```bash
python3 scripts/build_home.py
python3 scripts/build_about.py
python3 scripts/build_services.py
python3 scripts/build_contact.py
python3 scripts/build_posts.py
```

از ریشهٔ ریپو اجرا شود.

## قوانین کار (برای انسان و AI)

1. **تغییر متن یا سئو** → از پنل ادمین یا مستقیم `content/*.json` → بعد build → commit
2. **تغییر ظاهر/چیدمان** → `templates/*.html` و در صورت نیاز `styles.css` → بعد build → commit
3. **فایل‌های HTML نهایی را دستی منبع حقیقت ندانید**؛ خروجی build هستند
4. دامنه: `https://savehphysio.ir/` — ریپو: `sajad33b/savehphysio` — شاخه: `main`

## هدف‌های بعدی

- تکمیل و بهبود ظاهر پنل (نزدیک‌تر به حس بیان)
- خودکارسازی build بعد از ذخیره در پنل (GitHub Actions)
- اضافه کردن آمار ساده
- بعداً مهاجرت محتوا/سئو به هاست وردپرس با همان فیلدهای JSON

## ارجاع در چت جدید با Grok

کافی است بگویید:

> طبق `PROJECT.md` روی savehphysio کار کن.

یا:

> متن را در content/home.json عوض کن و build بگیر.

## تلفن‌ها (استاندارد)
- ثابت بین‌المللی: `tel:+988642230300`
- موبایل: `tel:+989015555721`
