#!/usr/bin/env python3
"""templates/testimonials.html + content/testimonials.json → reviews.html"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "content" / "testimonials.json"
TPL = ROOT / "templates" / "testimonials.html"
OUT = ROOT / "reviews.html"


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


def stars(n: int) -> str:
    n = max(0, min(5, int(n or 0)))
    return "★" * n + "☆" * (5 - n)


def render_list(items: list) -> str:
    if not items:
        return '<p class="review-empty">هنوز نظر منتشرشده‌ای ثبت نشده است. اولین نفری باشید که نظر می‌دهد.</p>'
    parts = ['<div class="reviews-grid">']
    for it in items:
        if it.get("hidden"):
            continue
        name = esc(it.get("name") or "مراجع")
        text = esc(it.get("text") or "")
        rating = it.get("rating") or 5
        date = esc(it.get("date") or "")
        parts.append(
            f'<article class="review-card">'
            f'<div class="stars" aria-label="امتیاز {rating} از ۵">{stars(rating)}</div>'
            f'<p class="text">{text}</p>'
            f'<div class="who">{name}' + (f" · {date}" if date else "") + "</div>"
            f"</article>"
        )
    parts.append("</div>")
    return "\n".join(parts)


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    seo = data.get("seo", {})
    page = data.get("page", {})
    form = data.get("form", {})
    items = data.get("items") or []

    schema = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": page.get("h1") or seo.get("title"),
        "description": seo.get("description"),
        "url": seo.get("canonical"),
        "inLanguage": "fa-IR",
        "isPartOf": {
            "@type": "WebSite",
            "name": "فیزیوتراپی ساوه | کلینیک ابن‌سینا",
            "url": "https://savehphysio.ir/",
        },
    }

    html = TPL.read_text(encoding="utf-8")
    repl = {
        "REVIEWS_TITLE": esc(seo.get("title", "نظرات")),
        "REVIEWS_DESCRIPTION": esc(seo.get("description", "")),
        "REVIEWS_OG_TITLE": esc(seo.get("og_title") or seo.get("title", "")),
        "REVIEWS_OG_DESCRIPTION": esc(seo.get("og_description") or seo.get("description", "")),
        "REVIEWS_OG_IMAGE": esc(seo.get("og_image", "https://savehphysio.ir/clinic.jpg")),
        "REVIEWS_CANONICAL": esc(seo.get("canonical", "https://savehphysio.ir/reviews.html")),
        "REVIEWS_TWITTER_TITLE": esc(seo.get("twitter_title") or seo.get("title", "")),
        "REVIEWS_TWITTER_DESCRIPTION": esc(
            seo.get("twitter_description") or seo.get("description", "")
        ),
        "REVIEWS_TWITTER_IMAGE": esc(
            seo.get("twitter_image") or seo.get("og_image", "https://savehphysio.ir/clinic.jpg")
        ),
        "REVIEWS_H1": esc(page.get("h1", "نظرات بیماران")),
        "REVIEWS_INTRO": esc(page.get("intro", "")),
        "REVIEWS_LIST": render_list(items),
        "REVIEWS_FORM_EMAIL": esc(form.get("email", "physiotherapyiran1401@gmail.com")),
        "REVIEWS_SUBMIT_LABEL": esc(form.get("submit_label", "ارسال نظر")),
        "REVIEWS_SUCCESS_MESSAGE": esc(
            form.get("success_message", "نظر شما دریافت شد.")
        ),
        "REVIEWS_SCHEMA_JSON": json.dumps(schema, ensure_ascii=False, indent=2),
    }
    for k, v in repl.items():
        html = html.replace(k, v)
    OUT.write_text(html, encoding="utf-8")
    print(f"OK → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
