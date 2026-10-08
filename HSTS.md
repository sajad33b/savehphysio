# فعال‌سازی HSTS برای savehphysio.ir

سایت از طریق Cloudflare به GitHub Pages وصل است. هدر HSTS باید در پنل Cloudflare فعال شود (از سمت HTML ممکن نیست).

## مسیر در Cloudflare

1. وارد [dash.cloudflare.com](https://dash.cloudflare.com) شوید
2. دامنه **savehphysio.ir** را انتخاب کنید
3. بروید به: **SSL/TLS → Edge Certificates**
4. بخش **HTTP Strict Transport Security (HSTS)** را پیدا کنید
5. **Enable HSTS** را بزنید با این تنظیمات پیشنهادی:

| تنظیم | مقدار پیشنهادی |
|--------|----------------|
| Max Age | 6 months (یا 12 months بعد از اطمینان) |
| Include subdomains | روشن (اگر همه زیر دامنه‌ها HTTPS دارند) |
| Preload | بعد از چند هفته پایدار بودن HTTPS، روشن کنید |
| No-Sniff | روشن |

6. ذخیره کنید و چند دقیقه صبر کنید
7. با این دستور بررسی کنید:

```bash
curl -sI https://savehphysio.ir | grep -i strict
```

باید چیزی شبیه این ببینید:

```
strict-transport-security: max-age=15552000; includeSubDomains
```

## هشدار

قبل از Preload مطمئن شوید کل سایت و زیر دامنه‌ها فقط با HTTPS کار می‌کنند. برگشت از preload سخت است.
