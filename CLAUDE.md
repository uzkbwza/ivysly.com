# ivysly.com

Personal website for Ivy Sly. Static site built with **ivygen**, a custom Python build system.

## Build Commands

```bash
./venv/bin/python3 -m ivygen build --dev   # Dev build (file:// URLs)
./venv/bin/python3 -m ivygen build          # Production build
./venv/bin/python3 -m ivygen watch          # Watch + auto-rebuild + dev server
./venv/bin/python3 -m ivygen serve          # Dev server on port 8000
./venv/bin/python3 -m ivygen new <collection> <title>  # Create new content
./venv/bin/python3 -m ivygen clean          # Clean output directory
./deploy.sh                                 # Build + rsync to production
```

## Project Structure

```
config.py              # Site config: collections, pages, URLs, navigation
ivygen/                # Custom static site generator
  cli.py               #   CLI (click): build, serve, watch, new, clean
  models.py            #   Data models: Collection, ContentItem, Page, Tag, Site
  parsing.py           #   Frontmatter + markdown parsing
  building.py          #   Build pipeline: discover, resolve, copy, render
  rendering.py         #   Jinja2 template rendering, RSS generation
content/               # Source content (markdown)
  blog/                #   Blog posts
  dream/               #   Dream journal entries (largest collection)
  games/               #   Game pages
  reviews/             #   Backloggd game reviews
  patchnotes/          #   HUSTLE patch notes
  misc/                #   Miscellaneous entries
  pages/               #   Standalone pages (about.md, music.md)
  images/              #   Content images (copied to output/images/)
  static/              #   Static files (copied to output/static/)
theme/
  templates/           #   Jinja2 templates
  static/css/          #   Stylesheets
  static/js/           #   comments.js (Bluesky), relativetime.js
  static/images/       #   Favicons, backgrounds, home section art
  static/font/         #   CJK fonts (MS Gothic, MS PGothic, mingliu)
output/                # Generated site (do not edit directly)
```

## Content Format

Pelican-style frontmatter (Key: Value pairs) followed by markdown body:

```markdown
Title: My Post Title
Date: 2025-02-10
Tags: tag1, tag2
Slug: custom-slug
Comments: 3lyuf3rxi322r

Post body in markdown...
```

Metadata fields become template attributes via `ContentItem.__getattr__` (e.g., `{{ article.cover }}`, `{{ article.steam }}`).

## Collections

Defined in `config.py` COLLECTIONS list. Each specifies source dir, templates, output URLs, and RSS feed path.

| Collection   | Source             | Item Template   | List Template   | Has Tags |
|--------------|--------------------|-----------------|-----------------|----------|
| dream        | content/dream      | dream.html      | dreamlog.html   | Yes      |
| blog         | content/blog       | blogpost.html   | blog.html       | No       |
| games        | content/games      | game.html       | gamelist.html   | No       |
| reviews      | content/reviews    | review.html     | reviewlist.html | No       |
| patchnotes   | content/patchnotes | patchnotes.html | None            | No       |
| misc         | content/misc       | miscentry.html  | misc.html       | No       |

## Template Pages

Rendered directly from Jinja2 (no markdown source):
- `home.html` → `index.html`
- `friends.html` → `misc/friends.html`
- `pixel-game-resolution-finder.html` → `misc/pixel-game-resolution-finder.html`

## Key Patterns

- Game covers: `{{ article.cover }}` — path starts with `./`, no `HTML_SITEURL` prefix
- Bluesky comments: `Comments: <bluesky-post-id>` in frontmatter, loaded by `comments.js`
- Pelican compat: templates use `article` (alias for `item`), `articles_page.object_list`
- Tags are per-collection namespaced (only dream collection uses tags currently)
- `article.html` and `category.html` templates are Pelican compatibility routers

## Utility Scripts

- `dream_watcher.py` — Discord bot (`!dream`, `!send dream|blog`, `!overwrite dream|blog`)
- `add_comments.py` — CLI to add Bluesky post IDs to content frontmatter
- `scrape_backloggd.py` — Scrapes game reviews from Backloggd into `content/reviews/`
