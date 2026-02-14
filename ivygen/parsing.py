"""Content parsing: frontmatter and markdown rendering."""

from __future__ import annotations
import re
from datetime import datetime
from html import unescape
from pathlib import Path
from typing import Any

import markdown
from slugify import slugify as python_slugify

from .models import Collection, ContentItem, Page


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    return python_slugify(text, lowercase=True)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """
    Parse Pelican-style frontmatter (Key: Value lines until blank line).

    Returns (metadata_dict, body_text).
    """
    lines = text.split('\n')
    meta: dict[str, Any] = {}
    body_start = 0

    for i, line in enumerate(lines):
        # Blank line marks end of frontmatter
        if not line.strip():
            body_start = i + 1
            break

        # Key: Value format
        if ':' in line:
            key, _, value = line.partition(':')
            key = key.strip().lower()
            value = value.strip()

            # Parse boolean values
            if value.lower() == 'true':
                meta[key] = True
            elif value.lower() == 'false':
                meta[key] = False
            else:
                meta[key] = value
        else:
            # Line without colon might be start of body
            body_start = i
            break

    # Normalize ./ paths to absolute /
    for key, value in meta.items():
        if isinstance(value, str) and value.startswith('./'):
            meta[key] = '/' + value[2:]

    body = '\n'.join(lines[body_start:])
    return meta, body


def parse_date(date_str: str) -> datetime:
    """Parse date string in various formats."""
    formats = [
        '%Y-%m-%d',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d %H:%M:%S',
        '%d %B %Y',
        '%d %b %Y',
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    # Default to epoch if unparseable
    return datetime(1970, 1, 1)


def render_markdown(text: str) -> str:
    """Render markdown to HTML."""
    md = markdown.Markdown(
        extensions=[
            'fenced_code',
            'tables',
            'smarty',
            'codehilite',
        ],
        extension_configs={
            'codehilite': {
                'css_class': 'highlight',
                'guess_lang': False,
            }
        }
    )
    return md.convert(text)


def extract_summary(html: str, max_length: int = 200) -> str:
    """Extract a plain-text summary from HTML content."""
    # Strip HTML tags
    text = re.sub(r'<[^>]+>', '', html)
    # Unescape HTML entities
    text = unescape(text)
    # Normalize whitespace
    text = ' '.join(text.split())
    # Truncate
    if len(text) > max_length:
        text = text[:max_length].rsplit(' ', 1)[0] + '...'
    return text


def parse_content_file(path: Path, collection: Collection) -> ContentItem:
    """Parse a markdown file into a ContentItem."""
    text = path.read_text(encoding='utf-8')

    # Split frontmatter from body
    meta, body = parse_frontmatter(text)

    # Generate slug from filename if not specified
    slug = meta.get('slug') or slugify(path.stem)

    # Parse date
    date = parse_date(meta.get('date', '1970-01-01'))

    # Render markdown to HTML
    html_content = render_markdown(body)

    # Generate summary
    summary = meta.get('summary') or extract_summary(html_content)

    # Build URL
    save_as = collection.item_url.format(
        collection=collection.name,
        slug=slug
    )
    url = save_as.removesuffix('.html')

    return ContentItem(
        title=meta.get('title', path.stem),
        slug=slug,
        date=date,
        content=html_content,
        raw_content=body,
        source_path=path,
        collection=collection,
        meta=meta,
        url=url,
        save_as=save_as,
        summary=summary,
        tags=[],  # Populated later during tag resolution
    )


def parse_page_file(path: Path, page_config: dict[str, Any]) -> Page:
    """Parse a markdown file into a Page."""
    text = path.read_text(encoding='utf-8')

    meta, body = parse_frontmatter(text)

    slug = meta.get('slug') or slugify(path.stem)
    html_content = render_markdown(body)
    summary = meta.get('summary') or extract_summary(html_content)

    save_as = page_config.get('url', f'{slug}.html')
    url = save_as.removesuffix('.html')

    return Page(
        title=meta.get('title', path.stem),
        slug=slug,
        template=page_config['template'],
        content=html_content,
        raw_content=body,
        source_path=path,
        meta=meta,
        url=url,
        save_as=save_as,
        summary=summary,
    )


def parse_tags_string(tags_str: str) -> list[str]:
    """Parse comma-separated tags string into list of tag names."""
    if not tags_str:
        return []
    return [t.strip() for t in tags_str.split(',') if t.strip()]
