#!/usr/bin/env python3
"""Scrape game reviews from Backloggd and generate content files for ivygen."""

import argparse
import re
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup, NavigableString
from slugify import slugify

BASE_URL = "https://backloggd.com"
USER = "ivysly"
REVIEWS_URL = f"{BASE_URL}/u/{USER}/reviews/"

CONTENT_DIR = Path(__file__).parent / "content" / "reviews"
IMAGES_DIR = Path(__file__).parent / "content" / "images" / "reviews"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
}


def fetch_page(url):
    """Fetch a page and return BeautifulSoup."""
    print(f"  Fetching {url}")
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def parse_review_list_page(soup):
    """Extract review entries from a review list page.

    All review cards (div.review-card) share a single parent div.col.
    Each card's game title is in the previous sibling div.game-name.
    Cover, status, date, and review link are inside the review-card div.
    """
    reviews = []

    for rc in soup.select("div.review-card"):
        entry = {}

        # Game name is the previous sibling div.game-name
        game_name_div = rc.find_previous_sibling("div", class_="game-name")
        if game_name_div:
            h3 = game_name_div.select_one("h3")
            entry["title"] = h3.get_text(strip=True) if h3 else ""
            yr = game_name_div.select_one("p.game-date")
            entry["year"] = yr.get_text(strip=True) if yr else ""
            # Game page URL
            game_link = game_name_div.select_one("a[href*='/games/']")
            entry["game_url"] = BASE_URL + game_link["href"] if game_link else ""
        else:
            continue

        if not entry["title"]:
            continue

        # Cover image inside the review card
        cover_img = rc.select_one('img[src*="images.igdb.com"]')
        entry["cover_url"] = cover_img["src"] if cover_img else ""

        # Review link
        link = rc.select_one("a.open-review-link")
        if link:
            entry["review_url"] = BASE_URL + link["href"]
        else:
            continue

        # Status from p.play-type
        status_el = rc.select_one("p.play-type")
        entry["status"] = status_el.get_text(strip=True) if status_el else ""

        # Date from time element
        time_el = rc.select_one("time[datetime]")
        entry["date_str"] = time_el["datetime"] if time_el else ""

        reviews.append(entry)

    return reviews


def node_to_markdown(node):
    """Convert an inline HTML node to markdown, preserving links/bold/italic."""
    if isinstance(node, NavigableString):
        return str(node)

    tag = node.name

    # Recurse into children first
    inner = "".join(node_to_markdown(c) for c in node.children)

    if tag == "a":
        href = node.get("href", "")
        if href and inner.strip():
            # Make relative URLs absolute
            if href.startswith("/"):
                href = BASE_URL + href
            return f"[{inner}]({href})"
        return inner
    if tag in ("b", "strong"):
        return f"**{inner}**"
    if tag in ("i", "em"):
        return f"*{inner}*"
    if tag == "u":
        return inner
    if tag == "br":
        return "\n"

    return inner


def parse_review_body(card_text):
    """Convert a review .card-text element into markdown with paragraphs."""
    paragraphs = []
    current = []
    br_count = 0

    for child in card_text.children:
        if child.name == "br":
            br_count += 1
            if br_count >= 2:
                text = "".join(current).strip()
                if text:
                    paragraphs.append(text)
                current = []
                br_count = 0
        else:
            br_count = 0
            current.append(node_to_markdown(child))

    text = "".join(current).strip()
    if text:
        paragraphs.append(text)

    return "\n\n".join(paragraphs)


def fetch_full_review(url):
    """Fetch the full review text from an individual review page.

    The review text is in div.review-body > .card-text.
    Paragraphs are separated by <br/><br/> tags.
    """
    soup = fetch_page(url)

    card_text = soup.select_one(".review-body .card-text")
    if not card_text:
        return ""

    return parse_review_body(card_text)


def parse_date(date_str):
    """Parse a date string into YYYY-MM-DD format."""
    date_str = date_str.strip()
    # Handle ISO format from datetime attribute (e.g. "2026-02-10T07:14:30Z")
    if "T" in date_str:
        date_str = date_str.split("T")[0]
    for fmt in ["%Y-%m-%d", "%b %d, %Y", "%b %d %Y", "%B %d, %Y"]:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str


def download_cover(cover_url, slug):
    """Download a cover image."""
    if not cover_url:
        return None

    # Ensure we get the big cover
    cover_url = cover_url.replace("t_cover_small", "t_cover_big")

    ext = ".jpg"
    if ".png" in cover_url.split("/")[-1]:
        ext = ".png"

    filepath = IMAGES_DIR / f"{slug}{ext}"

    print(f"  Downloading cover for {slug}")
    resp = requests.get(cover_url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    filepath.write_bytes(resp.content)

    return f"images/reviews/{slug}{ext}"


def fetch_game_page_info(game_url):
    """Fetch screenshot URL and full release date from a Backloggd game page.

    Returns (screenshot_url, release_date_str) where release_date_str is
    formatted as "dd Mon YYYY" or None if not found.
    """
    if not game_url:
        return None, None
    soup = fetch_page(game_url)

    # Screenshot
    screenshot_url = None
    img = soup.select_one('img[src*="t_screenshot"]')
    if img:
        url = img["src"]
        if url.startswith("//"):
            url = "https:" + url
        url = url.replace("t_screenshot_med", "t_screenshot_big")
        url = re.sub(r'\.webp$', '.jpg', url)
        screenshot_url = url

    # Release date - look for "Released <date>" text
    release_date = None
    for el in soup.find_all(string=re.compile(r'Released\s+')):
        text = el.strip() if isinstance(el, str) else el.get_text(strip=True)
        m = re.search(r'Released\s+(\w+\s+\d{1,2},?\s+\d{4})', text)
        if m:
            raw = m.group(1).replace(",", "")
            for fmt in ["%b %d %Y", "%B %d %Y"]:
                try:
                    release_date = datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
                    break
                except ValueError:
                    continue
            if release_date:
                break

    return screenshot_url, release_date


def fetch_screenshot_url(game_url):
    """Fetch a screenshot URL from a Backloggd game page."""
    screenshot_url, _ = fetch_game_page_info(game_url)
    return screenshot_url


def download_banner(screenshot_url, slug):
    """Download a screenshot as banner image."""
    if not screenshot_url:
        return None

    filepath = IMAGES_DIR / f"banner-{slug}.jpg"

    print(f"  Downloading banner for {slug}")
    resp = requests.get(screenshot_url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    filepath.write_bytes(resp.content)

    return f"images/reviews/banner-{slug}.jpg"


def generate_markdown(entry, review_text, cover_path, banner_path=None):
    """Generate a markdown file for a review."""
    slug = slugify(entry["title"])
    filepath = CONTENT_DIR / f"{slug}.md"

    lines = [f"Title: {entry['title']}"]

    date = parse_date(entry.get("date_str", ""))
    lines.append(f"Date: {date}")
    lines.append(f"Slug: {slug}")

    if cover_path:
        lines.append(f"Cover: ./{cover_path}")
    if banner_path:
        lines.append(f"Banner: ./{banner_path}")

    if entry.get("released"):
        lines.append(f"Released: {entry['released']}")
    if entry.get("review_url"):
        lines.append(f"Backloggd: {entry['review_url']}")

    lines.append("Comments:")
    lines.append("")
    lines.append(review_text)
    lines.append("")

    filepath.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Wrote {filepath.name}")
    return filepath


def scrape_all(force=False, min_length=450):
    """Main scraping loop."""
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    all_entries = []
    page = 1

    while True:
        url = REVIEWS_URL if page == 1 else f"{REVIEWS_URL}?page={page}"
        print(f"\nFetching review list page {page}...")
        soup = fetch_page(url)

        entries = parse_review_list_page(soup)
        if not entries:
            print(f"  No reviews found on page {page}, stopping.")
            break

        # Check for duplicates (last page might redirect)
        new_urls = {e["review_url"] for e in entries}
        existing_urls = {e["review_url"] for e in all_entries}
        if new_urls.issubset(existing_urls):
            print(f"  Page {page} has only duplicates, stopping.")
            break

        all_entries.extend(entries)
        print(f"  Found {len(entries)} reviews on page {page}")

        # Check for next page link
        has_next = False
        for a in soup.select("a"):
            href = a.get("href", "")
            text = a.get_text(strip=True).lower()
            if "next" in text or f"page={page + 1}" in href:
                has_next = True
                break

        if not has_next:
            break

        page += 1
        time.sleep(1.5)

    # Deduplicate
    seen = set()
    unique = []
    for e in all_entries:
        if e["review_url"] not in seen:
            seen.add(e["review_url"])
            unique.append(e)
    all_entries = unique

    print(f"\nTotal unique reviews found: {len(all_entries)}")

    # Process each review
    skipped_short = []
    written = 0
    for i, entry in enumerate(all_entries):
        slug = slugify(entry["title"])
        filepath = CONTENT_DIR / f"{slug}.md"

        if filepath.exists() and not force:
            print(f"\n[{i+1}/{len(all_entries)}] Skipping {entry['title']} (already exists)")
            continue

        print(f"\n[{i+1}/{len(all_entries)}] Processing: {entry['title']}")

        # Fetch full review text
        time.sleep(1.5)
        review_text = fetch_full_review(entry["review_url"])

        if len(review_text) < min_length:
            skipped_short.append((entry["title"], len(review_text), review_text[:100]))
            print(f"  SKIPPED (too short: {len(review_text)} chars)")
            continue

        # Download cover
        cover_path = download_cover(entry.get("cover_url"), slug)

        # Fetch screenshot and release date from game page
        banner_path = None
        if entry.get("game_url"):
            time.sleep(1.5)
            screenshot_url, release_date = fetch_game_page_info(entry["game_url"])
            banner_path = download_banner(screenshot_url, slug)
            if release_date:
                entry["released"] = release_date
            elif entry.get("year"):
                entry["released"] = entry["year"]

        # Generate markdown
        generate_markdown(entry, review_text, cover_path, banner_path)
        written += 1

        time.sleep(1)

    print(f"\n\nWrote {written} review files.")

    if skipped_short:
        print(f"Skipped {len(skipped_short)} short reviews:")
        for title, length, preview in skipped_short:
            print(f"  - {title} ({length} chars): {preview}...")


def scrape_single(url, force=False, min_length=450):
    """Scrape a single review from its URL."""
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Fetching review page: {url}")
    soup = fetch_page(url)

    # Game title from the game page link (e.g. /games/tomb-raider--8/)
    title_el = None
    for a in soup.select('a[href*="/games/"]'):
        href = a.get("href", "")
        if "/games/lib/" not in href and a.get_text(strip=True):
            title_el = a
            break
    if not title_el:
        print("Could not find game title on review page.")
        return
    title = title_el.get_text(strip=True)
    slug = slugify(title)

    filepath = CONTENT_DIR / f"{slug}.md"
    if filepath.exists() and not force:
        print(f"Skipping {title} (already exists, use --force to overwrite)")
        return

    # Cover image
    cover_url = ""
    cover_img = soup.select_one('img[src*="images.igdb.com"]')
    if cover_img:
        cover_url = cover_img["src"]

    # Date
    time_el = soup.select_one("time[datetime]")
    date_str = time_el["datetime"] if time_el else ""

    # Status
    status_el = soup.select_one("p.play-type")
    status = status_el.get_text(strip=True) if status_el else ""

    # Review text
    card_text = soup.select_one(".review-body .card-text")
    if not card_text:
        print("Could not find review text.")
        return

    review_text = parse_review_body(card_text)

    if len(review_text) < min_length:
        print(f"SKIPPED (too short: {len(review_text)} chars, min is {min_length})")
        return

    # Get game page URL for release date + banner
    game_url = None
    game_link = soup.select_one('a[href*="/games/"]')
    if game_link:
        href = game_link.get("href", "")
        if "/games/lib/" not in href:
            game_url = BASE_URL + href if href.startswith("/") else href

    # Fetch release date and screenshot from game page
    release_date = None
    banner_path = None
    if game_url:
        time.sleep(1.5)
        screenshot_url, release_date = fetch_game_page_info(game_url)
        if screenshot_url:
            banner_path = download_banner(screenshot_url, slug)

    entry = {
        "title": title,
        "date_str": date_str,
        "status": status,
        "cover_url": cover_url,
        "review_url": url,
        "released": release_date,
    }

    cover_path = download_cover(cover_url, slug)
    generate_markdown(entry, review_text, cover_path, banner_path)
    print("Done.")


def update_banners():
    """Download banners for existing reviews and update their markdown files.

    Scrapes the review list to get game page URLs, visits each game page
    for a screenshot, downloads it, and adds/updates Banner + Backloggd
    fields in existing markdown files.
    """
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    # Collect all entries from review list pages
    all_entries = []
    page = 1
    while True:
        url = REVIEWS_URL if page == 1 else f"{REVIEWS_URL}?page={page}"
        print(f"\nFetching review list page {page}...")
        soup = fetch_page(url)
        entries = parse_review_list_page(soup)
        if not entries:
            break
        new_urls = {e["review_url"] for e in entries}
        existing_urls = {e["review_url"] for e in all_entries}
        if new_urls.issubset(existing_urls):
            break
        all_entries.extend(entries)
        has_next = any(
            "next" in a.get_text(strip=True).lower() or f"page={page+1}" in a.get("href", "")
            for a in soup.select("a")
        )
        if not has_next:
            break
        page += 1
        time.sleep(1.5)

    # Build lookup by slug
    by_slug = {}
    for e in all_entries:
        s = slugify(e["title"])
        by_slug[s] = e

    # Process each existing markdown file
    for md_file in sorted(CONTENT_DIR.glob("*.md")):
        slug = md_file.stem
        entry = by_slug.get(slug)
        if not entry:
            print(f"\n  {slug}: no matching Backloggd entry, skipping")
            continue

        print(f"\n  Processing {slug}...")

        # Read existing file
        text = md_file.read_text(encoding="utf-8")
        lines = text.split("\n")

        # Find where metadata ends (first blank line)
        meta_end = 0
        for i, line in enumerate(lines):
            if line.strip() == "":
                meta_end = i
                break

        meta_lines = lines[:meta_end]
        body_lines = lines[meta_end:]

        # Remove old Banner/Backloggd/Status lines
        meta_lines = [l for l in meta_lines
                      if not l.startswith("Banner:") and
                         not l.startswith("Backloggd:") and
                         not l.startswith("Status:")]

        # Download banner if missing
        banner_file = IMAGES_DIR / f"banner-{slug}.jpg"
        if not banner_file.exists() and entry.get("game_url"):
            time.sleep(1.5)
            screenshot_url = fetch_screenshot_url(entry["game_url"])
            if screenshot_url:
                download_banner(screenshot_url, slug)
            else:
                print(f"    No screenshot found for {slug}")

        # Add Banner field after Cover line
        if banner_file.exists():
            banner_rel = f"./images/reviews/banner-{slug}.jpg"
            # Insert after Cover line, or after Slug line
            insert_idx = None
            for i, l in enumerate(meta_lines):
                if l.startswith("Cover:"):
                    insert_idx = i + 1
                    break
            if insert_idx is None:
                for i, l in enumerate(meta_lines):
                    if l.startswith("Slug:"):
                        insert_idx = i + 1
                        break
            if insert_idx is not None:
                meta_lines.insert(insert_idx, f"Banner: {banner_rel}")

        # Add Backloggd field before Comments line
        backloggd_url = entry.get("review_url", "")
        if backloggd_url:
            insert_idx = None
            for i, l in enumerate(meta_lines):
                if l.startswith("Comments:"):
                    insert_idx = i
                    break
            if insert_idx is not None:
                meta_lines.insert(insert_idx, f"Backloggd: {backloggd_url}")
            else:
                meta_lines.append(f"Backloggd: {backloggd_url}")

        new_text = "\n".join(meta_lines + body_lines)
        md_file.write_text(new_text, encoding="utf-8")
        print(f"    Updated {md_file.name}")

    print("\nDone updating banners.")


def main():
    parser = argparse.ArgumentParser(description="Scrape Backloggd reviews")
    parser.add_argument("--url", type=str,
                        help="Scrape a single review by URL")
    parser.add_argument("--force", "-f", action="store_true",
                        help="Overwrite existing files")
    parser.add_argument("--min-length", type=int, default=450,
                        help="Minimum review length in characters (default: 450)")
    parser.add_argument("--banners", action="store_true",
                        help="Download banners and update existing review files")
    args = parser.parse_args()

    if args.banners:
        update_banners()
    elif args.url:
        scrape_single(args.url, force=args.force, min_length=args.min_length)
    else:
        scrape_all(force=args.force, min_length=args.min_length)


if __name__ == "__main__":
    main()
