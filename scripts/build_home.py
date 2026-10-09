#!/usr/bin/env python3
"""
ساخت index.html از قالب + content/home.json
اجرا: python3 scripts/build_home.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "content" / "home.json"
TEMPLATE_PATH = ROOT / "templates" / "home.html"
OUTPUT_PATH = ROOT / "index.html"


def load_json() -> dict:
    with JSON_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def esc(s: str) -> str:
    if s is None:
        return ""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def replace_once(html: str, pattern: str, repl: str, flags=0) -> str:
    new, n = re.subn(pattern, repl, html, count=1, flags=flags)
    if n == 0:
        print(f"  warn: pattern not found: {pattern[:60]}...", file=sys.stderr)
    return new


def set_meta_content(html: str, *, name: str | None = None, prop: str | None = None, value: str) -> str:
    value = esc(value)
    if name:
        html = re.sub(
            rf'(<meta[^>]+name="{re.escape(name)}"[^>]+content=")[^"]*(")',
            rf"\1{value}\2",
            html,
            count=1,
        )
        html = re.sub(
            rf'(<meta[^>]+content=")[^"]*("[^>]+name="{re.escape(name)}")',
            rf"\1{value}\2",
            html,
            count=1,
        )
    if prop:
        html = re.sub(
            rf'(<meta[^>]+property="{re.escape(prop)}"[^>]+content=")[^"]*(")',
            rf"\1{value}\2",
            html,
            count=1,
        )
        html = re.sub(
            rf'(<meta[^>]+content=")[^"]*("[^>]+property="{re.escape(prop)}")',
            rf"\1{value}\2",
            html,
            count=1,
        )
    return html


def render_services(groups: list) -> str:
    parts = ['<div class="service-groups">']
    for g in groups:
        parts.append('<div class="service-group">')
        parts.append(f'<h3 class="service-group-title">{esc(g.get("title", ""))}</h3>')
        parts.append('<div class="service-grid">')
        for item in g.get("items", []):
            parts.append(
                '<div class="service-card">'
                f'<span class="service-title">{esc(item.get("title", ""))}</span>'
                f'<span class="service-desc">{esc(item.get("description", ""))}</span>'
                "</div>"
            )
        parts.append("</div></div>")
    parts.append("</div>")
    return "\n".join(parts)


def render_faq(items: list) -> str:
    parts = ['<div class="faq-list">']
    for it in items:
        q = esc(it.get("question", ""))
        a = esc(it.get("answer", ""))
        parts.append(
            '<details class="faq-item">'
            f'<summary><span class="faq-q">{q}</span><span class="faq-icon" aria-hidden="true">+</span></summary>'
            f"<p>{a}</p>"
            "</details>"
        )
    parts.append("</div>")
    return "\n".join(parts)


def render_testimonials(items: list) -> str:
    parts = ['<div class="testimonials-carousel" id="testimonials-carousel">']
    for i, it in enumerate(items):
        active = " is-active" if i == 0 else ""
        name = esc(it.get("name", ""))
        city = esc(it.get("city", "ساوه"))
        text = esc(it.get("text", ""))
        parts.append(
            f'<blockquote class="testimonial{active}" data-index="{i}">'
            f'<span class="testimonial-text">«{text}»</span>'
            f"<cite>{name}، {city}</cite>"
            "</blockquote>"
        )
    parts.append('<div class="testimonial-dots" role="tablist" aria-label="انتخاب نظر">')
    for i in range(len(items)):
        sel = ' aria-selected="true"' if i == 0 else ' aria-selected="false"'
        parts.append(
            f'<button type="button" class="dot{" is-active" if i == 0 else ""}" '
            f'data-index="{i}" role="tab"{sel} aria-label="نظر {i+1}"></button>'
        )
    parts.append("</div></div>")
    return "\n".join(parts)


def build() -> None:
    if not JSON_PATH.exists():
        sys.exit(f"missing {JSON_PATH}")
    if not TEMPLATE_PATH.exists():
        sys.exit(f"missing {TEMPLATE_PATH} — copy index.html to templates/home.html first")

    data = load_json()
    seo = data.get("seo", {})
    c = data.get("content", {})
    html = TEMPLATE_PATH.read_text(encoding="utf-8")

    # --- SEO ---
    if seo.get("title"):
        html = re.sub(r"<title>.*?</title>", f"<title>{esc(seo['title'])}</title>", html, count=1, flags=re.S)
    for key, attr in [
        ("description", ("name", "description")),
        ("og_title", ("property", "og:title")),
        ("og_description", ("property", "og:description")),
        ("og_image", ("property", "og:image")),
        ("twitter_title", ("name", "twitter:title")),
        ("twitter_description", ("name", "twitter:description")),
        ("twitter_image", ("name", "twitter:image")),
    ]:
        if seo.get(key):
            kind, name = attr
            if kind == "name":
                html = set_meta_content(html, name=name, value=seo[key])
            else:
                html = set_meta_content(html, prop=name, value=seo[key])
    if seo.get("canonical"):
        html = re.sub(
            r'(<link[^>]+rel="canonical"[^>]+href=")[^"]*(")',
            rf'\1{esc(seo["canonical"])}\2',
            html,
            count=1,
        )
        html = re.sub(
            r'(property="og:url"\s+content=")[^"]*(")',
            rf'\1{esc(seo["canonical"])}\2',
            html,
            count=1,
        )

    # --- Hero ---
    hero = c.get("hero", {})
    if hero.get("h1"):
        html = re.sub(r"<h1[^>]*>.*?</h1>", f"<h1>{esc(hero['h1'])}</h1>", html, count=1, flags=re.S)
    if hero.get("lead"):
        # first paragraph inside hero-ish area: replace first <p> after h1 in main
        html = re.sub(
            r"(<h1[^>]*>.*?</h1>\s*)<p[^>]*>.*?</p>",
            rf"\1<p>{esc(hero['lead'])}</p>",
            html,
            count=1,
            flags=re.S,
        )

    # --- About paragraphs (section about) ---
    about = c.get("about", {})
    if about.get("heading"):
        html = re.sub(
            r'(id="about"[\s\S]*?<h2>)[^<]*(</h2>)',
            rf"\1{esc(about['heading'])}\2",
            html,
            count=1,
        )
    paras = about.get("paragraphs") or []
    if paras:
        # replace consecutive <p> inside #about until next section heading services
        def about_repl(m):
            head = m.group(1)
            tail = m.group(3)
            body = "\n".join(f"<p>{esc(p)}</p>" for p in paras)
            return head + body + tail

        html = re.sub(
            r'(id="about"[\s\S]*?<h2>[^<]*</h2>\s*)([\s\S]*?)(\s*</div>\s*</div>\s*</section>|\s*</div>\s*</section>|\s*</div>\s*<section)',
            about_repl,
            html,
            count=1,
        )

    # --- Services ---
    services = c.get("services", {})
    if services.get("heading"):
        html = re.sub(
            r'(id="services"[\s\S]*?<h2>)[^<]*(</h2>)',
            rf"\1{esc(services['heading'])}\2",
            html,
            count=1,
        )
    if services.get("intro"):
        html = re.sub(
            r'(id="services"[\s\S]*?<h2>[^<]*</h2>\s*)<p[^>]*>.*?</p>',
            rf"\1<p style=\"color: var(--muted);margin:0;\">{esc(services['intro'])}</p>",
            html,
            count=1,
            flags=re.S,
        )
    if services.get("groups"):
        block = render_services(services["groups"])
        html = re.sub(
            r'<div class="service-groups">[\s\S]*?</div>\s*</div>\s*</div>\s*</section>',
            block + "\n</div>\n</div>\n</section>",
            html,
            count=1,
        )
        # fallback simpler
        if '<div class="service-groups">' in html and "service-group-title" in html:
            html2 = re.sub(
                r'<div class="service-groups">[\s\S]*?</div>(\s*</div>\s*</section>)',
                block + r"\1",
                html,
                count=1,
            )
            if html2 != html:
                html = html2

    # --- FAQ ---
    faq = c.get("faq", {})
    if faq.get("heading"):
        html = re.sub(
            r'(id="faq"[\s\S]*?<h2>)[^<]*(</h2>)',
            rf"\1{esc(faq['heading'])}\2",
            html,
            count=1,
        )
    if faq.get("intro"):
        html = re.sub(
            r'(id="faq"[\s\S]*?<h2>[^<]*</h2>\s*)<p[^>]*>.*?</p>',
            rf"\1<p style=\"color: var(--muted);margin:0;\">{esc(faq['intro'])}</p>",
            html,
            count=1,
            flags=re.S,
        )
    if faq.get("items"):
        block = render_faq(faq["items"])
        html = re.sub(r'<div class="faq-list">[\s\S]*?</div>', block, html, count=1)

    # --- Testimonials ---
    testi = c.get("testimonials", {})
    if testi.get("heading"):
        html = re.sub(
            r'(id="testimonials"[\s\S]*?<h2>)[^<]*(</h2>)',
            rf"\1{esc(testi['heading'])}\2",
            html,
            count=1,
        )
    if testi.get("intro"):
        html = re.sub(
            r'(id="testimonials"[\s\S]*?<h2>[^<]*</h2>\s*)<p[^>]*>.*?</p>',
            rf"\1<p style=\"color: var(--muted);margin:0;\">{esc(testi['intro'])}</p>",
            html,
            count=1,
            flags=re.S,
        )
    if testi.get("items"):
        block = render_testimonials(testi["items"])
        html = re.sub(
            r'<div class="testimonials-carousel"[\s\S]*?</div>\s*</div>\s*</section>',
            block + "\n</div>\n</section>",
            html,
            count=1,
        )
        html = re.sub(
            r'<div class="testimonials-carousel"[^>]*>[\s\S]*?</div>(\s*</div>\s*</section>)',
            block + r"\1",
            html,
            count=1,
        )

    # --- Contact ---
    contact = c.get("contact", {})
    if contact.get("heading"):
        html = re.sub(
            r'(id="contact"[\s\S]*?<h2>)[^<]*(</h2>)',
            rf"\1{esc(contact['heading'])}\2",
            html,
            count=1,
        )
    # phones - update visible text and hrefs carefully
    if contact.get("landline"):
        html = html.replace("۰۸۶۴۲۲۳۰۳۰۰", esc(contact["landline"]))
    if contact.get("landline_href"):
        html = re.sub(r'href="tel:\+?98[0-9+\-]*8642230300"', f'href="{esc(contact["landline_href"])}"', html)
    if contact.get("mobile"):
        html = html.replace("۰۹۰۱۵۵۵۵۷۲۱", esc(contact["mobile"]))
    if contact.get("mobile_href"):
        html = re.sub(r'href="tel:\+?989015555721"', f'href="{esc(contact["mobile_href"])}"', html)
    if contact.get("whatsapp_href"):
        html = re.sub(
            r'href="https://wa\.me/989015555721[^"]*"',
            f'href="{esc(contact["whatsapp_href"])}"',
            html,
        )
    if contact.get("address"):
        # replace common address patterns in contact/footer
        html = re.sub(
            r"ساوه،\s*خیابان جمهوری[^<]{0,80}",
            esc(contact["address"]),
            html,
            count=2,
        )
    if contact.get("hours"):
        html = re.sub(
            r"شنبه تا پنج‌شنبه[،:][^<]{0,40}",
            esc(contact["hours"]),
            html,
            count=3,
        )

    # --- Footer about ---
    footer = c.get("footer", {})
    if footer.get("about_short"):
        html = re.sub(
            r'(class="footer-brand"[\s\S]*?<p>)[\s\S]*?(</p>)',
            rf"\1{esc(footer['about_short'])}\2",
            html,
            count=1,
        )

    # --- Media alts ---
    media = c.get("media", {})
    for key, default_src in [
        ("logo_alt", "logo.png"),
        ("clinic_image_alt", "clinic.jpg"),
        ("profile_image_alt", "sajad-profile.jpg"),
    ]:
        alt = media.get(key)
        src = media.get(key.replace("_alt", "").replace("logo", "logo") if False else None)
    if media.get("logo_alt"):
        html = re.sub(
            r'(src="logo\.png"[^>]*alt=")[^"]*(")',
            rf"\1{esc(media['logo_alt'])}\2",
            html,
        )
        html = re.sub(
            r'(alt=")[^"]*("[^>]*src="logo\.png")',
            rf"\1{esc(media['logo_alt'])}\2",
            html,
        )
    if media.get("clinic_image_alt"):
        html = re.sub(
            r'(src="clinic\.jpg"[^>]*alt=")[^"]*(")',
            rf"\1{esc(media['clinic_image_alt'])}\2",
            html,
        )
        html = re.sub(
            r'(alt=")[^"]*("[^>]*src="clinic\.jpg")',
            rf"\1{esc(media['clinic_image_alt'])}\2",
            html,
        )
    if media.get("profile_image_alt"):
        html = re.sub(
            r'(src="sajad-profile\.jpg"[^>]*alt=")[^"]*(")',
            rf"\1{esc(media['profile_image_alt'])}\2",
            html,
        )
        html = re.sub(
            r'(alt=")[^"]*("[^>]*src="sajad-profile\.jpg")',
            rf"\1{esc(media['profile_image_alt'])}\2",
            html,
        )

    # brand name in footer strong
    brand = c.get("brand", {})
    if brand.get("physiotherapist_name"):
        html = re.sub(
            r'(class="footer-name">)[^<]+',
            rf"\1{esc(brand['physiotherapist_name'])}",
            html,
        )

    
    # --- Normalize phone hrefs (prevent double country code) ---
    html = html.replace("tel:+98+98", "tel:+98")
    html = html.replace("tel:+98086", "tel:+9886")
    html = re.sub(r'href="tel:\+98\+98([^"]*)"', r'href="tel:+98\1"', html)
    if contact.get("landline_href"):
        html = re.sub(
            r'href="tel:[^"]*8642230300"',
            f'href="{esc(contact["landline_href"])}"',
            html,
        )
    if contact.get("mobile_href"):
        html = re.sub(
            r'href="tel:[^"]*9015555721"',
            f'href="{esc(contact["mobile_href"])}"',
            html,
        )

    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"OK → {OUTPUT_PATH.relative_to(ROOT)} from {JSON_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    build()
