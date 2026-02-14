"""Jinja2 setup and template rendering."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element, SubElement, tostring

import jinja2

from .models import Collection, ContentItem, Page, Site, Tag, TemplatePage


class ArticlesPage:
    """Pelican-compatible pagination wrapper."""
    def __init__(self, items: list[ContentItem]):
        self.object_list = items


def setup_jinja_env(template_dir: Path) -> jinja2.Environment:
    """Set up Jinja2 environment with custom filters."""
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_dir)),
        autoescape=False,  # Pelican doesn't autoescape, content is pre-rendered HTML
    )

    # Custom filters
    env.filters['sort_by_article_count'] = lambda tags: sorted(
        tags, key=lambda t: len(t[1]), reverse=True
    )

    env.filters['striptags'] = strip_tags

    def strftime_filter(date_str, fmt='%d %b %Y'):
        """Parse a YYYY-MM-DD string and format it."""
        if not date_str:
            return ''
        from datetime import datetime
        for parse_fmt in ['%Y-%m-%d', '%d %b %Y', '%d %B %Y']:
            try:
                return datetime.strptime(str(date_str), parse_fmt).strftime(fmt)
            except ValueError:
                continue
        return str(date_str)

    env.filters['strftime'] = strftime_filter

    return env


def strip_tags(html: str) -> str:
    """Remove HTML tags from text."""
    import re
    return re.sub(r'<[^>]+>', '', html)


@dataclass
class RenderOutput:
    """Result of rendering a template."""
    content: str
    output_path: Path


def make_base_context(site: Site, dev_mode: bool = False) -> dict[str, Any]:
    """Create the base context available to all templates."""
    if dev_mode:
        siteurl = site.config.dev_url
        html_siteurl = site.config.dev_url
        sitehome = f"{site.config.dev_url}/" if site.config.dev_url else "/"
    else:
        siteurl = site.config.url
        html_siteurl = ""  # Use root-relative in production
        sitehome = "/"

    return {
        'site': site,
        'SITENAME': site.name,
        'SITEURL': siteurl,
        'HTML_SITEURL': html_siteurl,
        'SITEHOME': sitehome,
        'AUTHOR': site.author,
        'NAVIGATION_LINKS': site.config.navigation_links,

        # All collections available
        'collections': site.collections,

        # All tags (for tags.html)
        # Format: list of (tag_name, [items]) tuples for Pelican compatibility
        'tags': [
            (tag.name, tag.items)
            for coll in site.collections.values()
            for tag in coll.tags.values()
        ],
    }


def render_item(
    env: jinja2.Environment,
    site: Site,
    item: ContentItem,
    dev_mode: bool = False
) -> RenderOutput:
    """Render a single content item."""
    template = env.get_template(item.collection.item_template)

    context = make_base_context(site, dev_mode)
    context.update({
        'item': item,
        'article': item,  # Pelican compatibility
        'collection': item.collection,
        'category': item.collection.name.title(),  # Pelican compatibility
    })

    html = template.render(**context)
    output_path = site.config.output_dir / item.save_as

    return RenderOutput(content=html, output_path=output_path)


def render_collection_list(
    env: jinja2.Environment,
    site: Site,
    collection: Collection,
    dev_mode: bool = False
) -> RenderOutput | None:
    """Render a collection's list page."""
    if not collection.list_template or not collection.list_url:
        return None

    template = env.get_template(collection.list_template)

    context = make_base_context(site, dev_mode)

    # Collection-scoped tags as (name, items) tuples
    collection_tags = [
        (tag.name, tag.items)
        for tag in collection.tags.values()
    ]

    context.update({
        'items': collection.items,
        'articles': collection.items,  # Pelican compatibility
        'articles_page': ArticlesPage(collection.items),  # Pelican pagination compat
        'collection': collection,
        'category': collection.name.title(),
        'tags': collection_tags,  # Override global tags with collection-scoped
    })

    html = template.render(**context)
    output_path = site.config.output_dir / collection.list_url.format(
        collection=collection.name
    )

    return RenderOutput(content=html, output_path=output_path)


def render_tag_page(
    env: jinja2.Environment,
    site: Site,
    tag: Tag,
    dev_mode: bool = False
) -> RenderOutput | None:
    """Render a tag's listing page."""
    collection = tag.collection
    if not collection.tag_template or not collection.tag_url:
        return None

    template = env.get_template(collection.tag_template)

    context = make_base_context(site, dev_mode)

    # Collection-scoped tags
    collection_tags = [
        (t.name, t.items)
        for t in collection.tags.values()
    ]

    context.update({
        'tag': tag,
        'items': tag.items,
        'articles': tag.items,  # Pelican compatibility
        'collection': collection,
        'category': collection.name.title(),
        'tags': collection_tags,
    })

    html = template.render(**context)
    output_path = site.config.output_dir / tag.save_as

    return RenderOutput(content=html, output_path=output_path)


def render_tags_list(
    env: jinja2.Environment,
    site: Site,
    collection: Collection,
    dev_mode: bool = False
) -> RenderOutput | None:
    """Render the 'all tags' page for a collection."""
    if not collection.tags_list_template or not collection.tags_list_url:
        return None

    template = env.get_template(collection.tags_list_template)

    context = make_base_context(site, dev_mode)

    # Tags as (name, items) tuples for template compatibility
    collection_tags = [
        (tag.name, tag.items)
        for tag in collection.tags.values()
    ]

    context.update({
        'tags': collection_tags,
        'collection': collection,
        'category': collection.name.title(),
    })

    html = template.render(**context)
    output_path = site.config.output_dir / collection.tags_list_url

    return RenderOutput(content=html, output_path=output_path)


def render_page(
    env: jinja2.Environment,
    site: Site,
    page: Page,
    dev_mode: bool = False
) -> RenderOutput:
    """Render a standalone page."""
    template = env.get_template(page.template)

    context = make_base_context(site, dev_mode)
    context.update({
        'page': page,
    })

    html = template.render(**context)
    output_path = site.config.output_dir / page.save_as

    return RenderOutput(content=html, output_path=output_path)


def render_template_page(
    env: jinja2.Environment,
    site: Site,
    template_page: TemplatePage,
    dev_mode: bool = False
) -> RenderOutput:
    """Render a template directly (no markdown source)."""
    template = env.get_template(template_page.template)

    context = make_base_context(site, dev_mode)

    # Add all collections' items for templates like home.html that might need them
    for name, collection in site.collections.items():
        context[f'{name}_items'] = collection.items

    html = template.render(**context)

    return RenderOutput(content=html, output_path=template_page.output_path)


def render_rss_feed(
    site: Site,
    collection: Collection,
    dev_mode: bool = False
) -> RenderOutput | None:
    """Generate RSS feed for a collection."""
    if not collection.rss_enabled or not collection.rss_url:
        return None

    base_url = site.config.dev_url if dev_mode else site.config.url

    # Build RSS XML
    rss = Element('rss', version='2.0')
    channel = SubElement(rss, 'channel')

    SubElement(channel, 'title').text = f"{site.name} - {collection.name}"
    SubElement(channel, 'link').text = base_url
    SubElement(channel, 'description').text = f"{collection.name} feed"
    SubElement(channel, 'lastBuildDate').text = datetime.now().strftime(
        '%a, %d %b %Y %H:%M:%S +0000'
    )

    # Add items (limited)
    limit = site.config.rss_item_limit
    for item in collection.items[:limit]:
        rss_item = SubElement(channel, 'item')
        SubElement(rss_item, 'title').text = item.title
        SubElement(rss_item, 'link').text = f"{base_url}/{item.url}"
        SubElement(rss_item, 'description').text = item.content
        SubElement(rss_item, 'pubDate').text = item.date.strftime(
            '%a, %d %b %Y %H:%M:%S +0000'
        )
        SubElement(rss_item, 'guid').text = f"{base_url}/{item.url}"

    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(
        rss, encoding='unicode'
    )

    output_path = site.config.output_dir / collection.rss_url

    return RenderOutput(content=xml_content, output_path=output_path)


def render_all_rss_feed(site: Site, dev_mode: bool = False) -> RenderOutput:
    """Generate combined RSS feed for all collections."""
    base_url = site.config.dev_url if dev_mode else site.config.url

    rss = Element('rss', version='2.0')
    channel = SubElement(rss, 'channel')

    SubElement(channel, 'title').text = site.name
    SubElement(channel, 'link').text = base_url
    SubElement(channel, 'description').text = f"All content from {site.name}"
    SubElement(channel, 'lastBuildDate').text = datetime.now().strftime(
        '%a, %d %b %Y %H:%M:%S +0000'
    )

    # Collect all items from all collections
    all_items = []
    for collection in site.collections.values():
        if collection.rss_enabled:
            all_items.extend(collection.items)

    # Sort by date, newest first
    all_items.sort(key=lambda x: x.date, reverse=True)

    # Add items (limited)
    limit = site.config.rss_item_limit
    for item in all_items[:limit]:
        rss_item = SubElement(channel, 'item')
        SubElement(rss_item, 'title').text = item.title
        SubElement(rss_item, 'link').text = f"{base_url}/{item.url}"
        SubElement(rss_item, 'description').text = item.content
        SubElement(rss_item, 'pubDate').text = item.date.strftime(
            '%a, %d %b %Y %H:%M:%S +0000'
        )
        SubElement(rss_item, 'guid').text = f"{base_url}/{item.url}"

    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(
        rss, encoding='unicode'
    )

    output_path = site.config.output_dir / 'feeds' / 'all.rss.xml'

    return RenderOutput(content=xml_content, output_path=output_path)


def write_output(output: RenderOutput) -> None:
    """Write rendered content to file."""
    output.output_path.parent.mkdir(parents=True, exist_ok=True)
    output.output_path.write_text(output.content, encoding='utf-8')
