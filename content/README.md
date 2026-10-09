# محتوا و ساخت صفحه

## ساختار
- `content/home.json` — سئو + متن صفحه اول (منبع حقیقت)
- `templates/home.html` — قالب ظاهر و ساختار
- `scripts/build_home.py` — ساخت `index.html` از قالب + JSON
- `index.html` — خروجی نهایی (همان چیزی که روی سایت سرو می‌شود)

## گردش کار
1. متن یا سئو را در `content/home.json` عوض کنید
2. اجرا کنید:
   ```bash
   python3 scripts/build_home.py
   ```
3. `index.html` به‌روز می‌شود؛ بعد commit/push

## بعداً
- پنل ادمین می‌تواند همان `home.json` را ویرایش کند و build را صدا بزند
- مهاجرت وردپرس: فیلدهای JSON به برگه/بلوک نگاشت می‌شوند
