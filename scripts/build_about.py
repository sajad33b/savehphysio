#!/usr/bin/env python3
"""
ساخت صفحه درباره ما از templates/about.html + content/about.json
خروجی: about.html

اجرا: python3 scripts/build_about.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "content" / "about.json"
TEMPLATE_PATH = ROOT / "templates" / "about.html"
OUTPUT_PATH = ROOT / "about.html"


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


def render_sections(sections: list) -> str:
    parts: list[str] = []
    for sec in sections:
        heading = esc(sec.get("heading", ""))
        parts.append('<section class="page-section">')
        if heading:
            parts.append(f"<h2>{heading}</h2>")
        for p in sec.get("paragraphs", []):
            parts.append(f"<p>{esc(p)}</p>")
        parts.append("</section>")
    return "\n".join(parts)



def render_licenses(lic: dict) -> str:
    if not lic:
        return ""
    items = lic.get("items") or []
    if not items:
        return ""
    parts: list[str] = ['<section class="page-section licenses-section" id="licenses">']
    heading = esc(lic.get("heading", "مدارک و مجوزها"))
    parts.append(f"<h2>{heading}</h2>")
    intro = lic.get("intro")
    if intro:
        parts.append(f'<p class="licenses-intro">{esc(intro)}</p>')
    parts.append('<div class="licenses-grid">')
    for it in items:
        src = esc(it.get("src", ""))
        webp = esc(it.get("src_webp", ""))
        thumb = esc(it.get("thumb") or src)
        title = esc(it.get("title", ""))
        desc = esc(it.get("desc", ""))
        alt = esc(it.get("alt") or title)
        parts.append('<figure class="license-card">')
        parts.append(f'<a href="{src}" target="_blank" rel="noopener noreferrer" class="license-link">')
        if webp:
            parts.append(
                "<picture>"
                f'<source type="image/webp" srcset="{webp}">'
                f'<img src="{thumb}" alt="{alt}" width="420" height="300" loading="lazy" decoding="async">'
                "</picture>"
            )
        else:
            parts.append(
                f'<img src="{thumb}" alt="{alt}" width="420" height="300" loading="lazy" decoding="async">'
            )
        parts.append("</a>")
        parts.append(f"<figcaption><strong>{title}</strong>")
        if desc:
            parts.append(f"<span>{desc}</span>")
        parts.append("</figcaption></figure>")
    parts.append("</div></section>")
    return chr(10).join(parts)


def build_schema(data: dict) -> str:
    brand = data.get("brand", {})
    seo = data.get("seo", {})
    schema = {
        "@context": "https://schema.org",
        "@type": "AboutPage",
        "name": data.get("page", {}).get("h1") or seo.get("title"),
        "description": seo.get("description"),
        "url": seo.get("canonical", "https://savehphysio.ir/about.html"),
        "mainEntity": {
            "@type": "MedicalClinic",
            "name": brand.get("clinic_name", "کلینیک فیزیوتراپی ابن‌سینا ساوه"),
            "url": "https://savehphysio.ir/",
            "employee": {
                "@type": "Person",
                "name": brand.get("physiotherapist_name", "سجاد علی‌کرمی"),
                "jobTitle": brand.get("role", "فیزیوتراپیست"),
            },
        },
        "inLanguage": "fa-IR",
    }
    return json.dumps(schema, ensure_ascii=False, indent=2)


def build() -> None:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    seo = data.get("seo", {})
    page = data.get("page", {})
    brand = data.get("brand", {})
    cta = data.get("cta", {})

    html = TEMPLATE_PATH.read_text(encoding="utf-8")
    repl = {
        "ABOUT_TITLE": esc(seo.get("title", "")),
        "ABOUT_DESCRIPTION": esc(seo.get("description", "")),
        "ABOUT_OG_TITLE": esc(seo.get("og_title") or seo.get("title", "")),
        "ABOUT_OG_DESCRIPTION": esc(seo.get("og_description") or seo.get("description", "")),
        "ABOUT_OG_IMAGE": esc(seo.get("og_image", "https://savehphysio.ir/clinic.jpg")),
        "ABOUT_CANONICAL": esc(seo.get("canonical", "https://savehphysio.ir/about.html")),
        "ABOUT_TWITTER_TITLE": esc(seo.get("twitter_title") or seo.get("title", "")),
        "ABOUT_TWITTER_DESCRIPTION": esc(
            seo.get("twitter_description") or seo.get("description", "")
        ),
        "ABOUT_TWITTER_IMAGE": esc(
            seo.get("twitter_image") or seo.get("og_image", "https://savehphysio.ir/clinic.jpg")
        ),
        "ABOUT_H1": esc(page.get("h1", "")),
        "ABOUT_LEAD": esc(page.get("lead", "")),
        "ABOUT_PHYSIO_NAME": esc(brand.get("physiotherapist_name", "")),
        "ABOUT_ROLE": esc(brand.get("role", "فیزیوتراپیست")),
        "ABOUT_CLINIC": esc(brand.get("clinic_name", "")),
        "ABOUT_MEDICAL_ID": esc(brand.get("medical_id", "")),
        "ABOUT_MEDICAL_URL": esc(brand.get("medical_id_url", "#")),
        "ABOUT_SECTIONS": render_sections(data.get("sections", [])) + "\n" + render_licenses(data.get("licenses") or {}),
        "ABOUT_CTA_TEXT": esc(cta.get("text", "")),
        "ABOUT_TEL_LABEL": esc(cta.get("tel_label", "تماس")),
        "ABOUT_TEL_HREF": esc(cta.get("tel_href", "tel:+989015555721")),
        "ABOUT_WA_LABEL": esc(cta.get("wa_label", "واتساپ")),
        "ABOUT_WA_HREF": esc(cta.get("wa_href", "https://wa.me/989015555721")),
        "ABOUT_SCHEMA_JSON": build_schema(data),
    }
    for key, val in repl.items():
        html = html.replace(key, val)

    import re as _re

    left = _re.findall(r"ABOUT_[A-Z0-9_]+", html)
    if left:
        print(f"warn: unreplaced placeholders: {sorted(set(left))}", file=sys.stderr)

    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"OK → {OUTPUT_PATH.relative_to(ROOT)} from {JSON_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    build()
