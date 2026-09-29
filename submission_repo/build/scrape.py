"""Scraper. Workshop 1 block 4.

Crawl both websites, extract readable text as structured sections, and
collect image records in the same pass. Run this file directly to
(re)build data/pages.json and data/images.json.

Check for /sitemap.xml before writing a crawler. If it exists it lists
every page and you can skip the crawl entirely.
"""
import json
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

SITES = [
    # TODO: the two Inno Wing sites you were given
    "https://innowings.engg.hku.hk/innowing1/",
    "https://innoacademy.engg.hku.hk",
]

HEADING_MAX_LEN = 120


def crawl(start_url: str, max_pages: int = 500) -> list[str]:
    """Return every page URL on the same site as start_url."""
    seen, queue, out = set(), [start_url], []
    domain = urlparse(start_url).netloc

    while queue and len(out) < max_pages:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        try:
            html = requests.get(url, timeout=20).text
        except Exception:
            continue
        out.append(url)

        # TODO find the links on this page and add the internal ones to
        # TODO queue, something like:
        # for a in BeautifulSoup(html, "html.parser").select("a[href]"):
        #     link = urljoin(url, a["href"]).split("#")[0]
        #     if urlparse(link).netloc == domain and link not in seen:
        #         queue.append(link)

    return out


def _norm(text: str) -> str:
    return " ".join(text.split()).strip()


def is_fully_hidden(el: Tag) -> bool:
    # Parent decompose() can leave child Tags with attrs=None still in a
    # previously-materialized select() list.
    if not isinstance(el, Tag) or el.attrs is None:
        return False
    cls = set(el.get("class") or [])
    return (
        "elementor-hidden-desktop" in cls
        and "elementor-hidden-tablet" in cls
        and ("elementor-hidden-mobile" in cls or "elementor-hidden-phone" in cls)
    )


def _clean_root(root: Tag) -> None:
    for sel in (
        "script",
        "style",
        "noscript",
        ".elementor-swiper-button",
        ".elementor-widget-spacer",
    ):
        for node in root.select(sel):
            node.decompose()
    # Sort with deepest first so removing a parent does not invalidate a later sibling
    # check on an already-detached child.
    sections = list(root.select("section.elementor-section"))
    sections.sort(key=lambda s: len(list(s.parents)), reverse=True)
    for section in sections:
        # some sections are fully hidden in the website but they can be seen by the web crawler
        # since they only introduce noise and do not contain any useful information
        # , they are removed here
        if is_fully_hidden(section):
            section.decompose()


def _widget_type(widget: Tag) -> str:
    classes = widget.get("class") or []
    for c in classes:
        if c.startswith("elementor-widget-") and c != "elementor-widget":
            return c.removeprefix("elementor-widget-")
    return widget.get("data-widget_type", "").split(".")[0]


def _heading_text(widget: Tag) -> str:
    title = widget.select_one(".elementor-heading-title")
    if title:
        return _norm(title.get_text(" ", strip=True))
    for tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        h = widget.find(tag)
        if h:
            return _norm(h.get_text(" ", strip=True))
    return _norm(widget.get_text(" ", strip=True))


def _text_editor_body(widget: Tag) -> str:
    parts = []
    for p in widget.find_all("p"):
        t = _norm(p.get_text(" ", strip=True))
        if t:
            parts.append(t)
    if parts:
        return " ".join(parts)
    return _norm(widget.get_text(" ", strip=True))


def _append_text(current: dict, text: str) -> None:
    text = _norm(text)
    if not text:
        return
    if current["text"]:
        current["text"] += " " + text
    else:
        current["text"] = text


def _flush(sections: list[dict], current: dict) -> None:
    heading = _norm(current.get("heading", ""))
    text = _norm(current.get("text", ""))
    if heading or text:
        sections.append({"heading": heading, "text": text})


def _is_title_echo(section: dict, page_title: str) -> bool:
    """True for empty sections that only repeat the document <title>."""
    title = _norm(page_title)
    heading = _norm(section.get("heading", ""))
    text = _norm(section.get("text", ""))
    return bool(title) and not text and heading == title


def _build_sections(root: Tag, page_title: str) -> list[dict]:
    sections: list[dict] = []
    # Do not seed with page_title: that produced an empty first section that
    # only echoed <title> before the first real heading flushed it.
    current = {"heading": "", "text": ""}

    widgets = root.select(
        ".elementor-widget-heading, "
        ".elementor-widget-theme-post-title, "
        ".elementor-widget-text-editor, "
        ".elementor-widget-posts, "
        ".elementor-widget-image-carousel, "
        ".elementor-widget-slides"
    )

    for widget in widgets:
        wtype = _widget_type(widget)

        if wtype in ("heading", "theme-post-title"):
            text = _heading_text(widget)
            if not text:
                continue
            if len(text) <= HEADING_MAX_LEN:
                _flush(sections, current)
                current = {"heading": text, "text": ""}
            else:
                # Long "heading" widgets are body prose (e.g. Wing About).
                _append_text(current, text)
            continue

        if wtype == "text-editor":
            _append_text(current, _text_editor_body(widget))
            continue

        if wtype == "posts":
            for article in widget.select("article"):
                h = article.find(["h1", "h2", "h3", "h4", "h5", "h6"])
                if not h:
                    continue
                heading = _norm(h.get_text(" ", strip=True))
                if not heading:
                    continue
                _flush(sections, current)
                body_parts = []
                for p in article.find_all("p"):
                    t = _norm(p.get_text(" ", strip=True))
                    if t:
                        body_parts.append(t)
                current = {"heading": heading, "text": " ".join(body_parts)}
            continue

        if wtype == "image-carousel":
            for cap in widget.select(".elementor-image-carousel-caption"):
                _append_text(current, cap.get_text(" ", strip=True))
            continue

        if wtype == "slides":
            for slide in widget.select(".elementor-slide-heading"):
                _append_text(current, slide.get_text(" ", strip=True))
            continue

    _flush(sections, current)
    return [
        s for s in sections
        if (s["heading"] or s["text"]) and not _is_title_echo(s, page_title)
    ]


def _collect_images(root: Tag, url: str) -> list[dict]:
    images = []
    for img in root.select("img"):
        src = img.get("src")
        if not src:
            continue
        fig = img.find_parent("figure")
        caption = ""
        if fig and fig.find("figcaption"):
            caption = _norm(fig.find("figcaption").get_text(" ", strip=True))
        if not caption:
            # Elementor carousels often put captions next to the image.
            sib = img.find_next_sibling(class_="elementor-image-carousel-caption")
            if sib:
                caption = _norm(sib.get_text(" ", strip=True))
        images.append({
            "src": urljoin(url, src),
            "alt": img.get("alt",""),
            "caption": caption,
            "page": url,
        })
    return images


def extract(html: str, url: str) -> dict:
    """Return {"url", "title", "sections", "images"} for one page.

    Scope to #content so site header/nav and footer never enter the
    corpus. Split Elementor widgets into heading/body sections so the
    indexer can prepend section context to each chunk.
    """
    soup = BeautifulSoup(html, "html.parser")
    title = _norm(soup.title.get_text(" ", strip=True)) if soup.title else ""

    root = soup.select_one("#content .elementor") or soup.select_one("#content")
    if root is None:
        return {"url": url, "title": title, "sections": [], "images": []}

    _clean_root(root)
    sections = _build_sections(root, title)
    images = _collect_images(root, url)

    return {
        "url": url,
        "title": title,
        "sections": sections,
        "images": images,
    }


if __name__ == "__main__":
    pages = []
    for site in SITES:
        for url in crawl(site):
            try:
                pages.append(extract(requests.get(url, timeout=20).text, url))
            except Exception as exc:
                print("skipped", url, exc)

    Path("data").mkdir(exist_ok=True)
    Path("data/pages.json").write_text(json.dumps(pages, indent=1))

    images = [im for p in pages for im in p["images"]]
    Path("data/images.json").write_text(json.dumps(images, indent=1))

    print(f"{len(pages)} pages, {len(images)} images")
    for p in pages:
        print(f"  {p['url']}: {len(p['sections'])} sections")
