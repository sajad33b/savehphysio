#!/usr/bin/env python3
"""
ساخت صفحه تماس از templates/contact.html + content/contact.json
خروجی: contact.html

اجرا: python3 scripts/build_contact.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "content" / "contact.json"
TEMPLATE_PATH = ROOT / "templates" / "contact.html"
OUTPUT_PATH = ROOT / "contact.html"


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


def build_schema(data: dict) -> str:
    seo = data.get("seo", {})
    c = data.get("contact", {})
    schema = {
        "@context": "https://schema.org",
        "@type": "ContactPage",
        "name": data.get("page", {}).get("h1") or seo.get("title"),
        "description": seo.get("description"),
        "url": seo.get("canonical", "https://savehphysio.ir/contact.html"),
        "mainEntity": {
            "@type": "MedicalClinic",
            "name": "کلینیک فیزیوتراپی ابن‌سینا ساوه",
            "url": "https://savehphysio.ir/",
            "telephone": [
                c.get("landline_href", "").replace("tel:", ""),
                c.get("mobile_href", "").replace("tel:", ""),
            ],
            "address": {
                "@type": "PostalAddress",
                "streetAddress": c.get("address", ""),
                "addressLocality": "ساوه",
                "addressRegion": "مرکزی",
                "addressCountry": "IR",
            },
            "geo": {
                "@type": "GeoCoordinates",
                "latitude": c.get("map_lat"),
                "longitude": c.get("map_lng"),
            },
            "openingHours": c.get("hours"),
        },
        "inLanguage": "fa-IR",
    }
    return json.dumps(schema, ensure_ascii=False, indent=2)


def build() -> None:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    seo = data.get("seo", {})
    page = data.get("page", {})
    c = data.get("contact", {})

    html = TEMPLATE_PATH.read_text(encoding="utf-8")
    repl = {
        "CONTACT_TITLE": esc(seo.get("title", "")),
        "CONTACT_DESCRIPTION": esc(seo.get("description", "")),
        "CONTACT_OG_TITLE": esc(seo.get("og_title") or seo.get("title", "")),
        "CONTACT_OG_DESCRIPTION": esc(seo.get("og_description") or seo.get("description", "")),
        "CONTACT_OG_IMAGE": esc(seo.get("og_image", "https://savehphysio.ir/clinic.jpg")),
        "CONTACT_CANONICAL": esc(seo.get("canonical", "https://savehphysio.ir/contact.html")),
        "CONTACT_TWITTER_TITLE": esc(seo.get("twitter_title") or seo.get("title", "")),
        "CONTACT_TWITTER_DESCRIPTION": esc(
            seo.get("twitter_description") or seo.get("description", "")
        ),
        "CONTACT_TWITTER_IMAGE": esc(
            seo.get("twitter_image") or seo.get("og_image", "https://savehphysio.ir/clinic.jpg")
        ),
        "CONTACT_H1": esc(page.get("h1", "")),
        "CONTACT_INTRO": esc(page.get("intro", "")),
        "CONTACT_LANDLINE": esc(c.get("landline", "")),
        "CONTACT_LANDLINE_HREF": esc(c.get("landline_href", "tel:+988642230300")),
        "CONTACT_MOBILE": esc(c.get("mobile", "")),
        "CONTACT_MOBILE_HREF": esc(c.get("mobile_href", "tel:+989015555721")),
        "CONTACT_WA_LABEL": esc(c.get("whatsapp_label", "واتساپ")),
        "CONTACT_WA_HREF": esc(c.get("whatsapp_href", "https://wa.me/989015555721")),
        "CONTACT_IG": esc(c.get("instagram", "")),
        "CONTACT_IG_URL": esc(c.get("instagram_url", "https://www.instagram.com/savehphysio")),
        "CONTACT_TG_URL": esc(c.get("telegram_url", "https://t.me/savehphysio")),
        "CONTACT_BALE_URL": esc(c.get("bale_url", "https://ble.ir/savehphysio")),
        "CONTACT_RUBIKA_URL": esc(c.get("rubika_url", "https://rubika.ir/savehphysio")),
        "CONTACT_ADDRESS": esc(c.get("address", "")),
        "CONTACT_HOURS": esc(c.get("hours", "")),
        "CONTACT_MAP_EMBED": esc(
            c.get("map_embed")
            or f"https://www.google.com/maps?q={c.get('map_lat')},{c.get('map_lng')}&z=16&output=embed"
        ),
        "CONTACT_SCHEMA_JSON": build_schema(data),
    }
    for key in sorted(repl.keys(), key=len, reverse=True):
        html = html.replace(key, repl[key])

    left = re.findall(r"CONTACT_[A-Z0-9_]+", html)
    if left:
        print(f"warn: unreplaced placeholders: {sorted(set(left))}", file=sys.stderr)

    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"OK → {OUTPUT_PATH.relative_to(ROOT)} from {JSON_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    build()
