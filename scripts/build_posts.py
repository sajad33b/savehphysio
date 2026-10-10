#!/usr/bin/env python3
"""
ساخت صفحات مقاله از templates/post.html + content/posts/*.json
خروجی: blog/{slug}.html

اجرا:
  python3 scripts/build_posts.py
  python3 scripts/build_posts.py dard-siatik-chist   # فقط یک پست
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "content" / "posts"
TEMPLATE_PATH = ROOT / "templates" / "post.html"
OUT_DIR = ROOT / "blog"


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


def render_body(blocks: list) -> str:
    parts: list[str] = []
    for b in blocks:
        t = b.get("type", "p")
        text = esc(b.get("text", ""))
        if t == "h2":
            parts.append(f"<h2>{text}</h2>")
        elif t == "h3":
            parts.append(f"<h3>{text}</h3>")
        else:
            parts.append(f"<p>{text}</p>")
    return "\n".join(parts)


def render_tags(tags: list) -> str:
    return "".join(f"<span>{esc(t)}</span>" for t in tags)


def build_schema(data: dict) -> str:
    seo = data.get("seo", {})
    post = data.get("post", {})
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": post.get("h1") or seo.get("title"),
        "description": seo.get("description"),
        "datePublished": post.get("published"),
        "dateModified": post.get("updated") or post.get("published"),
        "author": {
            "@type": "Person",
            "name": post.get("author", "سجاد علی‌کرمی"),
        },
        "publisher": {
            "@type": "MedicalClinic",
            "name": "کلینیک فیزیوتراپی ابن‌سینا ساوه",
            "url": "https://savehphysio.ir/",
        },
        "mainEntityOfPage": seo.get("canonical"),
        "image": seo.get("og_image"),
        "inLanguage": "fa-IR",
    }
    return json.dumps(schema, ensure_ascii=False, indent=2)


def build_one(json_path: Path) -> Path:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    seo = data.get("seo", {})
    post = data.get("post", {})
    slug = post.get("slug") or json_path.stem
    rel = post.get("related_service") or {}

    html = TEMPLATE_PATH.read_text(encoding="utf-8")
    repl = {
        "POST_TITLE": esc(seo.get("title", "")),
        "POST_DESCRIPTION": esc(seo.get("description", "")),
        "POST_OG_TITLE": esc(seo.get("og_title") or seo.get("title", "")),
        "POST_OG_DESCRIPTION": esc(seo.get("og_description") or seo.get("description", "")),
        "POST_OG_IMAGE": esc(seo.get("og_image", "https://savehphysio.ir/clinic.jpg")),
        "POST_CANONICAL": esc(seo.get("canonical", f"https://savehphysio.ir/blog/{slug}.html")),
        "POST_TWITTER_TITLE": esc(seo.get("twitter_title") or seo.get("title", "")),
        "POST_TWITTER_DESCRIPTION": esc(
            seo.get("twitter_description") or seo.get("description", "")
        ),
        "POST_TWITTER_IMAGE": esc(
            seo.get("twitter_image") or seo.get("og_image", "https://savehphysio.ir/clinic.jpg")
        ),
        "POST_H1": esc(post.get("h1", "")),
        "POST_AUTHOR": esc(post.get("author", "")),
        "POST_DATE": esc(post.get("published", "")),
        "POST_CATEGORY": esc(post.get("category", "")),
        "POST_BREADCRUMB": esc(post.get("h1", "")[:40]),
        "POST_BODY": render_body(post.get("body", [])),
        "POST_TAGS": render_tags(post.get("tags", [])),
        "POST_SERVICE_LABEL": esc(rel.get("label", "مشاهده خدمات")),
        "POST_SERVICE_HREF": esc(rel.get("href", "../#services")),
        "POST_SCHEMA_JSON": build_schema(data),
    }
    for key, val in repl.items():
        html = html.replace(key, val)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{slug}.html"
    out.write_text(html, encoding="utf-8")
    return out


def main() -> None:
    only = sys.argv[1] if len(sys.argv) > 1 else None
    files = sorted(POSTS_DIR.glob("*.json"))
    files = [f for f in files if f.name != "index.json"]
    if only:
        files = [f for f in files if f.stem == only or f.name == only]
        if not files:
            print(f"not found: {only}", file=sys.stderr)
            sys.exit(1)
    if not files:
        print("no posts in content/posts/", file=sys.stderr)
        sys.exit(1)
    for f in files:
        out = build_one(f)
        print(f"OK → {out.relative_to(ROOT)} from {f.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
