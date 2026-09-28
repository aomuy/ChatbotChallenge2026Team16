"""Scraper. Workshop 1 block 4.

Crawl both websites, extract readable text as structured sections, and
collect image records in the same pass. Run this file directly to
(re)build data/pages.json and data/images.json.

Both permitted sites are WordPress and publish /sitemap.xml, which
redirects to /wp-sitemap.xml. That index lists every page, so this
scraper reads the sitemap and does not follow links. A breadth-first
crawler remains only as a fallback if the sitemap is missing.
"""
import json
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree as ET

import requests
from bs4 import BeautifulSoup, Tag

# Official permitted sources from the challenge page:
# https://innowings.engg.hku.hk/innowing1/
# https://innoacademy.engg.hku.hk/
SITES = [
    "https://innowings.engg.hku.hk/innowing1/",
    "https://innoacademy.engg.hku.hk/",
]

HEADING_MAX_LEN = 120
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
# Archive pages repeat post excerpts already stored as their own URLs.
ARCHIVE_ROOTS = {"author", "tag", "category", "wp-json"}
# Safety cap for a broken sitemap or a crawler loop. Both real sitemaps
# are well under this (about 1,200 content URLs together).
MAX_PAGES = 2000
HEADERS = {"User-Agent": "HKU-ChatbotChallenge-Team16/1.0 (course project)"}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def _origin(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _canonical(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def _in_scope(url: str, start_url: str) -> bool:
    """Keep HTML pages on this host. Drop archives and Wing Two.

    The Innovation Wing sitemap covers the whole domain, including
    Innovation Wing Two. The permitted source is Wing One only
    (https://innowings.engg.hku.hk/innowing1/). Project posts live at
    the domain root rather than under /innowing1/, so those stay in;
    paths that name Wing Two are dropped.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    if parsed.netloc != urlparse(start_url).netloc:
        return False
    if parsed.path.lower().endswith((
        ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg",
        ".pdf", ".zip", ".mp4", ".mp3", ".css", ".js",
    )):
        return False
    parts = [part for part in parsed.path.split("/") if part]
    if parts and parts[0] in ARCHIVE_ROOTS:
        return False
    if parsed.netloc == "innowings.engg.hku.hk":
        path = parsed.path.lower()
        if "/innowing2" in path or "/innowing-two" in path:
            return False
    return True


def _sitemap_locs(xml_bytes: bytes) -> tuple[str, list[str]]:
    root = ET.fromstring(xml_bytes)
    kind = root.tag.rsplit("}", 1)[-1]
    locs = [
        node.text.strip()
        for node in root.findall(".//sm:loc", SITEMAP_NS)
        if node.text and node.text.strip()
    ]
    return kind, locs


def urls_from_sitemap(start_url: str) -> list[str] | None:
    """Return page URLs from /sitemap.xml, or None if it is not there.

    WordPress serves a sitemap index. /sitemap.xml redirects to
    /wp-sitemap.xml, whose children are the post, page, and archive lists.
    """
    origin = _origin(start_url)
    try:
        response = SESSION.get(f"{origin}/sitemap.xml", timeout=30)
        response.raise_for_status()
    except requests.RequestException:
        return None
    if "xml" not in response.headers.get("Content-Type", "") and not response.content.lstrip().startswith(b"<?xml"):
        return None

    try:
        kind, locs = _sitemap_locs(response.content)
    except ET.ParseError:
        return None

    page_urls: list[str] = []
    pending = locs if kind == "sitemapindex" else []
    if kind == "urlset":
        page_urls.extend(locs)

    seen_maps = set()
    while pending:
        map_url = pending.pop(0)
        if map_url in seen_maps:
            continue
        seen_maps.add(map_url)
        try:
            child = SESSION.get(map_url, timeout=30)
            child.raise_for_status()
            child_kind, child_locs = _sitemap_locs(child.content)
        except (requests.RequestException, ET.ParseError):
            continue
        if child_kind == "sitemapindex":
            pending.extend(child_locs)
        else:
            page_urls.extend(child_locs)

    deduped = []
    seen = set()
    for url in page_urls:
        if not _in_scope(url, start_url):
            continue
        key = _canonical(url)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(url.split("#")[0])
    return deduped


def _crawl_links(start_url: str, max_pages: int) -> list[str]:
    """Breadth-first fallback used only when a site has no sitemap."""
    seen, queue, out = set(), [start_url], []
    domain = urlparse(start_url).netloc

    while queue and len(out) < max_pages:
        url = queue.pop(0)
        key = _canonical(url)
        if key in seen:
            continue
        seen.add(key)
        try:
            html = SESSION.get(url, timeout=20).text
        except requests.RequestException:
            continue
        out.append(url.split("#")[0])

        for anchor in BeautifulSoup(html, "html.parser").select("a[href]"):
            link = urljoin(url, anchor["href"]).split("#")[0].split("?")[0]
            if urlparse(link).netloc == domain and _canonical(link) not in seen:
                if _in_scope(link, start_url):
                    queue.append(link)

    return out


def crawl(start_url: str, max_pages: int = MAX_PAGES) -> list[str]:
    """Return page URLs for start_url's site.

    Prefer the sitemap. Link-following is the fallback.
    """
    sitemap_urls = urls_from_sitemap(start_url)
    if sitemap_urls:
        print(f"sitemap {start_url}: {len(sitemap_urls)} urls")
        if len(sitemap_urls) > max_pages:
            print(f"capping {len(sitemap_urls)} urls at {max_pages}")
        return sitemap_urls[:max_pages]
    print(f"no sitemap for {start_url}; crawling links")
    return _crawl_links(start_url, max_pages)


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


def _write_corpus(pages: list[dict]) -> None:
    Path("data").mkdir(exist_ok=True)
    Path("data/pages.json").write_text(
        json.dumps(pages, indent=1, ensure_ascii=False)
    )
    images = [im for page in pages for im in page["images"]]
    Path("data/images.json").write_text(
        json.dumps(images, indent=1, ensure_ascii=False)
    )


if __name__ == "__main__":
    pages = []
    for site in SITES:
        urls = crawl(site)
        for i, url in enumerate(urls, start=1):
            try:
                response = SESSION.get(url, timeout=20)
                response.raise_for_status()
                pages.append(extract(response.text, url))
            except Exception as exc:
                print("skipped", url, exc)
            if i % 50 == 0 or i == len(urls):
                _write_corpus(pages)
                print(f"  fetched {i}/{len(urls)} from {site}", flush=True)
            time.sleep(0.15)

    _write_corpus(pages)
    images = [im for page in pages for im in page["images"]]
    nonempty = sum(1 for page in pages if page["sections"])
    print(f"{len(pages)} pages ({nonempty} with text), {len(images)} images", flush=True)
