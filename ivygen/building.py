"""Content discovery, tag resolution, and build pipeline."""

from __future__ import annotations
import shutil
from pathlib import Path
from typing import Any

from .models import (
    Collection, ContentItem, Page, Site, SiteConfig, Tag, TemplatePage
)
from .parsing import parse_content_file, parse_page_file, parse_tags_string, slugify


def load_config(config_path: Path) -> SiteConfig:
    """Load configuration from a Python config file."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("config", config_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Could not load config from {config_path}")

    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)

    base_dir = config_path.parent

    return SiteConfig(
        name=getattr(config_module, 'SITE_NAME', 'My Site'),
        url=getattr(config_module, 'SITE_URL', ''),
        dev_url=getattr(config_module, 'DEV_URL', ''),
        author=getattr(config_module, 'AUTHOR', ''),
        timezone=getattr(config_module, 'TIMEZONE', 'UTC'),
        content_dir=base_dir / getattr(config_module, 'CONTENT_DIR', 'content'),
        output_dir=base_dir / getattr(config_module, 'OUTPUT_DIR', 'output'),
        theme_dir=base_dir / getattr(config_module, 'THEME_DIR', 'theme'),
        static_dirs=[
            base_dir / d for d in getattr(config_module, 'STATIC_DIRS', ['content/static'])
        ],
        navigation_links=getattr(config_module, 'NAVIGATION_LINKS', []),
        collections=getattr(config_module, 'COLLECTIONS', []),
        pages=getattr(config_module, 'PAGES', {}),
        template_pages=getattr(config_module, 'TEMPLATE_PAGES', {}),
        rss_item_limit=getattr(config_module, 'RSS_ITEM_LIMIT', 100),
    )


def discover_collection(collection: Collection, base_dir: Path) -> list[ContentItem]:
    """Discover and parse all content files in a collection."""
    source_path = base_dir / collection.source_dir
    if not source_path.exists():
        return []

    items = []
    for path in source_path.glob('*.md'):
        try:
            item = parse_content_file(path, collection)
            # Skip drafts unless explicitly marked published
            status = item.meta.get('status', 'published')
            if status == 'draft':
                continue
            items.append(item)
        except Exception as e:
            print(f"Warning: Failed to parse {path}: {e}")

    return items


def resolve_tags(collection: Collection, items: list[ContentItem]) -> dict[str, Tag]:
    """Create Tag objects and link them to items."""
    tags: dict[str, Tag] = {}

    for item in items:
        tags_str = item.meta.get('tags', '')
        if isinstance(tags_str, str):
            tag_names = parse_tags_string(tags_str)
        else:
            tag_names = tags_str if tags_str else []

        for tag_name in tag_names:
            tag_slug = slugify(tag_name)

            if tag_slug not in tags:
                tags[tag_slug] = Tag(
                    name=tag_name,
                    slug=tag_slug,
                    collection=collection,
                    items=[],
                )

            tag = tags[tag_slug]
            tag.items.append(item)
            item.tags.append(tag)

    return tags


def sort_and_link(items: list[ContentItem], sort_by: str, reverse: bool) -> list[ContentItem]:
    """Sort items and set prev/next links."""
    def get_sort_key(item: ContentItem) -> Any:
        if sort_by == 'date':
            return item.date
        return item.meta.get(sort_by, 0)

    sorted_items = sorted(items, key=get_sort_key, reverse=reverse)

    # Link prev/next
    for i, item in enumerate(sorted_items):
        if i > 0:
            item.next_item = sorted_items[i - 1]  # Newer item
        if i < len(sorted_items) - 1:
            item.prev_item = sorted_items[i + 1]  # Older item

    return sorted_items


def discover_pages(config: SiteConfig) -> dict[str, Page]:
    """Discover and parse all pages."""
    pages = {}
    base_dir = config.content_dir.parent

    for name, page_config in config.pages.items():
        source_path = base_dir / page_config['source']
        if source_path.exists():
            try:
                page = parse_page_file(source_path, page_config)
                pages[name] = page
            except Exception as e:
                print(f"Warning: Failed to parse page {source_path}: {e}")

    return pages


def create_template_pages(config: SiteConfig) -> list[TemplatePage]:
    """Create TemplatePage objects for direct template rendering."""
    return [
        TemplatePage(
            template=template,
            url=output_url,
            output_path=config.output_dir / output_url,
        )
        for template, output_url in config.template_pages.items()
    ]


def clean_output(output_dir: Path, preserve: list[str]) -> None:
    """Clean output directory, preserving specified paths."""
    if not output_dir.exists():
        return

    preserve_set = set(preserve)

    for child in output_dir.iterdir():
        if child.name in preserve_set:
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def copy_static(src_dirs: list[Path], output_dir: Path) -> None:
    """Copy static files to output."""
    for src_dir in src_dirs:
        if not src_dir.exists():
            continue

        # Determine destination (static/ subdir)
        dest = output_dir / 'static'
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src_dir, dest)


def copy_theme_static(theme_static: Path, output_dir: Path) -> None:
    """Copy theme static files."""
    dest = output_dir / 'theme'
    if dest.exists():
        shutil.rmtree(dest)
    if theme_static.exists():
        shutil.copytree(theme_static, dest)


def copy_content_images(content_dir: Path, output_dir: Path) -> None:
    """Copy content/images to output/images."""
    src = content_dir / 'images'
    if not src.exists():
        return

    dest = output_dir / 'images'
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def build_site(config_path: Path, dev_mode: bool = False) -> Site:
    """Main build entry point."""
    print(f"Loading config from {config_path}...")
    config = load_config(config_path)

    base_dir = config_path.parent

    # Build collections
    print("Discovering content...")
    collections: dict[str, Collection] = {}

    for coll_config in config.collections:
        collection = Collection(
            name=coll_config['name'],
            source_dir=coll_config['source_dir'],
            item_template=coll_config['item_template'],
            list_template=coll_config.get('list_template'),
            tag_template=coll_config.get('tag_template'),
            tags_list_template=coll_config.get('tags_list_template'),
            item_url=coll_config.get('item_url', '{collection}/{slug}.html'),
            list_url=coll_config.get('list_url'),
            tag_url=coll_config.get('tag_url'),
            tags_list_url=coll_config.get('tags_list_url'),
            rss_enabled=coll_config.get('rss_enabled', False),
            rss_url=coll_config.get('rss_url'),
            sort_by=coll_config.get('sort_by', 'date'),
            sort_reverse=coll_config.get('sort_reverse', True),
            optional_fields=coll_config.get('optional_fields', {}),
        )

        # Discover items
        items = discover_collection(collection, base_dir)
        print(f"  {collection.name}: {len(items)} items")

        # Resolve tags
        if collection.tag_template:
            tags = resolve_tags(collection, items)
            collection.tags = tags
            print(f"    {len(tags)} tags")

        # Sort and link
        sorted_items = sort_and_link(items, collection.sort_by, collection.sort_reverse)
        collection.items = sorted_items

        collections[collection.name] = collection

    # Discover pages
    pages = discover_pages(config)
    print(f"Pages: {len(pages)}")

    # Template pages
    template_pages = create_template_pages(config)

    # Build all tags index
    all_tags = {
        name: coll.tags
        for name, coll in collections.items()
        if coll.tags
    }

    site = Site(
        config=config,
        collections=collections,
        pages=pages,
        template_pages=template_pages,
        all_tags=all_tags,
    )

    return site
