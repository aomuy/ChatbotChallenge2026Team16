"""Scraper. Workshop 1 block 4.

Crawl both websites, extract readable text as structured sections, and
collect image records in the same pass. Run this file directly to
(re)build data/pages.json and data/images.json.

Check for /sitemap.xml before writing a crawler. If it exists it lists
every page and you can skip the crawl entirely.
"""
import json
from pathlib import Path
from urllib.parse import (
    parse_qsl,
    unquote,
    urlencode,
    urljoin,
    urlparse,
    urlunparse,
)

import requests
from bs4 import BeautifulSoup, Tag

SITES = [
    # TODO: the two Inno Wing sites you were given
    "https://innowings.engg.hku.hk/innowing1/",
    "https://innoacademy.engg.hku.hk",
]

HEADING_MAX_LEN = 120

# Dropped from query strings; they create clone URLs for the same page.
_TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
}

# Linked media must not be crawled as HTML pages (pages.json had ~500 of these).
_SKIP_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".svg",
    ".ico",
    ".pdf",
    ".zip",
    ".css",
    ".js",
    ".mp3",
    ".mp4",
    ".wav",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
}


def normalize_url(url: str) -> str | None:
    """Canonical form for crawl dedupe, or None if the URL is not a page.

    Handles scheme/host casing, default ports, fragments, tracking query
    params, percent-decoding, collapsed slashes, trailing slashes on
    directory paths, and skips obvious non-HTML assets.
    """
    if not url:
        return None
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https"):
        return None

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    if "@" in netloc:
        netloc = netloc.rsplit("@", 1)[-1]
    if scheme == "http" and netloc.endswith(":80"):
        netloc = netloc[:-3]
    elif scheme == "https" and netloc.endswith(":443"):
        netloc = netloc[:-4]

    path = unquote(parsed.path) or "/"
    while "//" in path:
        path = path.replace("//", "/")
    # Broken href text sometimes ends up in the path.
    if "opens in a new tab" in path.lower():
        return None

    last = path.rsplit("/", 1)[-1]
    if "." in last:
        ext = "." + last.rsplit(".", 1)[-1].lower()
        if ext in _SKIP_EXTENSIONS:
            return None
        # File-like path: no trailing slash.
    else:
        # Directory-like path: WordPress canonicals here use a trailing slash.
        if not path.endswith("/"):
            path += "/"

    if "/wp-content/uploads/" in path:
        return None

    query_items = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k.lower() not in _TRACKING_PARAMS
    ]
    query = urlencode(query_items, doseq=True)
    # Fragment intentionally dropped — same document.
    return urlunparse((scheme, netloc, path, "", query, ""))


def _canonical_href(html: str, base_url: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    link = soup.find(
        "link",
        rel=lambda value: value
        and "canonical" in [str(part).lower() for part in (
            value if isinstance(value, list) else [value]
        )],
    )
    if not link or not link.get("href"):
        return None
    return normalize_url(urljoin(base_url, link["href"]))


def crawl(start_url: str, max_pages: int = 500) -> list[str]:
    """Return every page URL on the same site as start_url."""
    start = normalize_url(start_url)
    if not start:
        return []

    seen, stored, queue, out = set(), set(), [start], []
    domain = urlparse(start).netloc

    while queue and len(out) < max_pages:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        try:
            resp = requests.get(url, timeout=20, allow_redirects=True)
            resp.raise_for_status()
        except Exception:
            continue

        # Prefer redirect target, then <link rel="canonical"> when same-host.
        # That merges /acrylic vs /acrylic/ and /equipment/ vs /innowing1/equipment/.
        final = normalize_url(resp.url)
        if not final or urlparse(final).netloc != domain:
            continue
        identity = _canonical_href(resp.text, final) or final
        if urlparse(identity).netloc != domain:
            identity = final

        seen.add(final)
        seen.add(identity)
        if identity not in stored:
            stored.add(identity)
            out.append(identity)

        for a in BeautifulSoup(resp.text, "html.parser").select("a[href]"):
            href = a.get("href")
            if not href:
                continue
            link = normalize_url(urljoin(final, href))
            if link and urlparse(link).netloc == domain and link not in seen:
                queue.append(link)

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
    seen_pages: set[str] = set()
    for site in SITES:
        for url in crawl(site):
            if url in seen_pages:
                continue
            try:
                resp = requests.get(url, timeout=20, allow_redirects=True)
                resp.raise_for_status()
                # Re-resolve in case the live site redirects again on the
                # second fetch; keep one record per normalized identity.
                final = normalize_url(resp.url) or url
                identity = _canonical_href(resp.text, final) or final
                if identity in seen_pages:
                    continue
                seen_pages.add(identity)
                pages.append(extract(resp.text, identity))
            except Exception as exc:
                print("skipped", url, exc)

    Path("data").mkdir(exist_ok=True)
    Path("data/pages.json").write_text(json.dumps(pages, indent=1))

    images = [im for p in pages for im in p["images"]]
    Path("data/images.json").write_text(json.dumps(images, indent=1))

    print(f"{len(pages)} pages, {len(images)} images")
    for p in pages:
        print(f"  {p['url']}: {len(p['sections'])} sections")
