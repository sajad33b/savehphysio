#!/usr/bin/env python3
"""ساخت صفحه خدمات — گروه‌بندی، شماره‌گذاری، ناوبری نقطه‌ای اسکرول"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "content" / "services.json"
TEMPLATE_PATH = ROOT / "templates" / "services.html"
OUTPUT_PATH = ROOT / "services.html"


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


def render_groups(groups: list) -> str:
    parts: list[str] = []
    n = 0
    for g in groups:
        gid = esc(g.get("id") or f"g{len(parts)}")
        title = esc(g.get("title", ""))
        parts.append(f'<section class="svc-group page-section" id="svc-{gid}" data-spy="{gid}">')
        parts.append(f'<h2 class="svc-group-title">{title}</h2>')
        parts.append('<div class="svc-grid">')
        for item in g.get("items", []):
            n += 1
            it = esc(item.get("title", ""))
            desc = esc(item.get("description", ""))
            parts.append(
                f'<div class="svc-card">'
                f'<span class="svc-num">{n:02d}</span>'
                f'<span class="title">{it}</span>'
                f'<span class="desc">{desc}</span>'
                f"</div>"
            )
        parts.append("</div></section>")
    return "\n".join(parts)


def render_spy(groups: list) -> str:
    parts = [
        '<nav class="svc-spy" aria-label="بخش‌های خدمات">',
        '<div class="svc-spy-track" aria-hidden="true"><div class="svc-spy-line"></div></div>',
    ]
    for g in groups:
        gid = esc(g.get("id") or "")
        title = esc(g.get("title", ""))
        parts.append(
            f'<a class="svc-spy-dot" href="#svc-{gid}" data-spy-target="{gid}" title="{title}">'
            f'<span class="svc-spy-point"></span>'
            f'<span class="svc-spy-label">{title}</span>'
            f"</a>"
        )
    parts.append("</nav>")
    return "\n".join(parts)


def build_schema(data: dict) -> str:
    seo = data.get("seo", {})
    page = data.get("page", {})
    items = []
    for g in data.get("groups", []):
        for it in g.get("items", []):
            items.append(
                {
                    "@type": "MedicalProcedure",
                    "name": it.get("title"),
                    "description": it.get("description"),
                }
            )
    schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": page.get("h1") or seo.get("title"),
        "description": seo.get("description"),
        "url": seo.get("canonical", "https://savehphysio.ir/services.html"),
        "mainEntity": {
            "@type": "ItemList",
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "item": it}
                for i, it in enumerate(items)
            ],
        },
        "isPartOf": {
            "@type": "MedicalClinic",
            "name": "کلینیک فیزیوتراپی ابن‌سینا ساوه",
            "url": "https://savehphysio.ir/",
        },
        "inLanguage": "fa-IR",
    }
    return json.dumps(schema, ensure_ascii=False, indent=2)


def build() -> None:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    seo = data.get("seo", {})
    page = data.get("page", {})
    cta = data.get("cta", {})
    groups = data.get("groups", [])

    html = TEMPLATE_PATH.read_text(encoding="utf-8")
    repl = {
        "SVC_TITLE": esc(seo.get("title", "")),
        "SVC_DESCRIPTION": esc(seo.get("description", "")),
        "SVC_OG_TITLE": esc(seo.get("og_title") or seo.get("title", "")),
        "SVC_OG_DESCRIPTION": esc(seo.get("og_description") or seo.get("description", "")),
        "SVC_OG_IMAGE": esc(seo.get("og_image", "https://savehphysio.ir/clinic.jpg")),
        "SVC_CANONICAL": esc(seo.get("canonical", "https://savehphysio.ir/services.html")),
        "SVC_TWITTER_TITLE": esc(seo.get("twitter_title") or seo.get("title", "")),
        "SVC_TWITTER_DESCRIPTION": esc(
            seo.get("twitter_description") or seo.get("description", "")
        ),
        "SVC_TWITTER_IMAGE": esc(
            seo.get("twitter_image") or seo.get("og_image", "https://savehphysio.ir/clinic.jpg")
        ),
        "SVC_H1": esc(page.get("h1", "")),
        "SVC_INTRO": esc(page.get("intro", "")),
        "SVC_SPY": render_spy(groups),
        "SVC_GROUPS": render_groups(groups),
        "SVC_CTA_TEXT": esc(cta.get("text", "")),
        "SVC_TEL_LABEL": esc(cta.get("tel_label", "تماس")),
        "SVC_TEL_HREF": esc(cta.get("tel_href", "tel:+989015555721")),
        "SVC_WA_LABEL": esc(cta.get("wa_label", "واتساپ")),
        "SVC_WA_HREF": esc(cta.get("wa_href", "https://wa.me/989015555721")),
        "SVC_SCHEMA_JSON": build_schema(data),
    }
    for key in sorted(repl.keys(), key=len, reverse=True):
        html = html.replace(key, repl[key])

    left = re.findall(r"SVC_[A-Z0-9_]+", html)
    if left:
        print(f"warn: unreplaced: {sorted(set(left))}", file=sys.stderr)

    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"OK → {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    build()
