"""Core data models for IvyGen."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class Collection:
    """A content collection (e.g., dream, blog, games)."""
    name: str
    source_dir: str

    # Templates
    item_template: str
    list_template: str | None = None
    tag_template: str | None = None
    tags_list_template: str | None = None  # For "all tags" page

    # URL patterns
    item_url: str = "{collection}/{slug}.html"
    list_url: str | None = "{collection}.html"
    tag_url: str | None = None
    tags_list_url: str | None = None

    # RSS
    rss_enabled: bool = False
    rss_url: str | None = None

    # Sorting
    sort_by: str = "date"
    sort_reverse: bool = True  # Newest first by default

    # Metadata
    required_fields: list[str] = field(default_factory=lambda: ["title"])
    optional_fields: dict[str, Any] = field(default_factory=dict)

    # Runtime data (populated during build)
    items: list[ContentItem] = field(default_factory=list, repr=False)
    tags: dict[str, Tag] = field(default_factory=dict, repr=False)


@dataclass
class ContentItem:
    """A single content item (article, dream, game, etc.)."""
    title: str
    slug: str
    date: datetime
    content: str  # Rendered HTML
    raw_content: str  # Original markdown body
    source_path: Path
    collection: Collection
    meta: dict[str, Any]  # All frontmatter metadata

    # Computed fields
    url: str = ""
    output_path: Path = field(default_factory=Path)
    summary: str = ""

    # Navigation (set after sorting)
    prev_item: ContentItem | None = field(default=None, repr=False)
    next_item: ContentItem | None = field(default=None, repr=False)

    # Tags (resolved after parsing)
    tags: list[Tag] = field(default_factory=list, repr=False)

    def __getattr__(self, name: str) -> Any:
        """Allow accessing metadata fields as attributes (for template compatibility)."""
        if name.startswith('_'):
            raise AttributeError(name)
        if 'meta' in self.__dict__ and name in self.meta:
            return self.meta[name]
        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")

    # Pelican compatibility aliases
    @property
    def prev_article_in_category(self) -> ContentItem | None:
        return self.prev_item

    @property
    def next_article_in_category(self) -> ContentItem | None:
        return self.next_item


@dataclass
class Tag:
    """A tag within a specific collection."""
    name: str
    slug: str
    collection: Collection
    items: list[ContentItem] = field(default_factory=list, repr=False)

    @property
    def url(self) -> str:
        if self.collection.tag_url:
            return self.collection.tag_url.format(
                collection=self.collection.name,
                slug=self.slug
            )
        return f"tag/{self.slug}.html"

    def __str__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash((self.name, self.collection.name))


@dataclass
class Page:
    """A standalone page (about, music, etc.)."""
    title: str
    slug: str
    template: str
    content: str
    raw_content: str
    source_path: Path
    meta: dict[str, Any]
    url: str = ""
    output_path: Path = field(default_factory=Path)
    summary: str = ""

    def __getattr__(self, name: str) -> Any:
        """Allow accessing metadata fields as attributes."""
        if name.startswith('_'):
            raise AttributeError(name)
        if 'meta' in self.__dict__ and name in self.meta:
            return self.meta[name]
        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")


@dataclass
class TemplatePage:
    """A template rendered directly (no markdown source)."""
    template: str
    url: str
    output_path: Path = field(default_factory=Path)


@dataclass
class SiteConfig:
    """Site-wide configuration."""
    name: str
    url: str
    dev_url: str
    author: str
    timezone: str

    content_dir: Path
    output_dir: Path
    theme_dir: Path
    static_dirs: list[Path]

    navigation_links: list[tuple[str, str]]

    collections: list[dict[str, Any]]
    pages: dict[str, dict[str, Any]]
    template_pages: dict[str, str]

    rss_item_limit: int = 100


@dataclass
class Site:
    """The complete site state during build."""
    config: SiteConfig
    collections: dict[str, Collection]
    pages: dict[str, Page]
    template_pages: list[TemplatePage]

    # Computed
    all_tags: dict[str, dict[str, Tag]] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def url(self) -> str:
        return self.config.url

    @property
    def author(self) -> str:
        return self.config.author
