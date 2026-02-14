"""Command-line interface for IvyGen."""

from __future__ import annotations
import http.server
import os
import socketserver
import sys
from datetime import datetime
from pathlib import Path

import click

from .building import (
    build_site, clean_output, copy_content_images, copy_static, copy_theme_static
)
from .rendering import (
    RenderOutput,
    render_all_rss_feed, render_collection_list, render_item, render_page,
    render_rss_feed, render_tag_page, render_tags_list, render_template_page,
    setup_jinja_env, write_output
)


@click.group()
def cli():
    """IvyGen - Static site generator for ivysly.com"""
    pass


@cli.command()
@click.option('--dev', is_flag=True, help='Development mode (local URLs)')
@click.option('--config', default='config.py', help='Config file path')
def build(dev: bool, config: str):
    """Build the site."""
    config_path = Path(config).resolve()

    if not config_path.exists():
        click.echo(f"Config file not found: {config_path}", err=True)
        sys.exit(1)

    # Build site data
    site = build_site(config_path, dev_mode=dev)

    # Setup Jinja
    template_dir = site.config.theme_dir / 'templates'
    env = setup_jinja_env(template_dir)

    # Clean output
    click.echo("Cleaning output directory...")
    clean_output(site.config.output_dir, preserve=['static'])

    # Render everything
    click.echo("Rendering content...")
    rendered_count = 0

    # Collection items
    for name, collection in site.collections.items():
        for item in collection.items:
            output = render_item(env, site, item, dev_mode=dev)
            write_output(output)
            rendered_count += 1

        # Collection list page
        list_output = render_collection_list(env, site, collection, dev_mode=dev)
        if list_output:
            write_output(list_output)
            rendered_count += 1
            # Also save as <dir>/index.html so /blog resolves to blog/index.html
            # (when both blog.html and blog/ directory exist)
            dir_path = list_output.output_path.with_suffix('')
            if dir_path.is_dir():
                index_output = RenderOutput(
                    content=list_output.content,
                    output_path=dir_path / 'index.html',
                )
                write_output(index_output)

        # Tag pages
        for tag in collection.tags.values():
            tag_output = render_tag_page(env, site, tag, dev_mode=dev)
            if tag_output:
                write_output(tag_output)
                rendered_count += 1

        # Tags list page
        tags_list_output = render_tags_list(env, site, collection, dev_mode=dev)
        if tags_list_output:
            write_output(tags_list_output)
            rendered_count += 1

        # RSS feed
        rss_output = render_rss_feed(site, collection, dev_mode=dev)
        if rss_output:
            write_output(rss_output)
            rendered_count += 1

    # All RSS feed
    all_rss_output = render_all_rss_feed(site, dev_mode=dev)
    write_output(all_rss_output)
    rendered_count += 1

    # Pages
    for page in site.pages.values():
        output = render_page(env, site, page, dev_mode=dev)
        write_output(output)
        rendered_count += 1

    # Template pages
    for template_page in site.template_pages:
        output = render_template_page(env, site, template_page, dev_mode=dev)
        write_output(output)
        rendered_count += 1

    # Copy static files
    click.echo("Copying static files...")
    copy_static(site.config.static_dirs, site.config.output_dir)
    copy_theme_static(site.config.theme_dir / 'static', site.config.output_dir)
    copy_content_images(site.config.content_dir, site.config.output_dir)

    click.echo(f"Build complete! {rendered_count} files rendered.")


@cli.command()
@click.option('--port', default=8000, help='Port to serve on')
@click.option('--config', default='config.py', help='Config file path')
def serve(port: int, config: str):
    """Start a local development server."""
    config_path = Path(config).resolve()

    if not config_path.exists():
        click.echo(f"Config file not found: {config_path}", err=True)
        sys.exit(1)

    # Load config to get output dir
    from .building import load_config
    site_config = load_config(config_path)

    output_dir = site_config.output_dir

    if not output_dir.exists():
        click.echo(f"Output directory not found: {output_dir}", err=True)
        click.echo("Run 'ivygen build --dev' first.")
        sys.exit(1)

    # Change to output directory
    os.chdir(output_dir)

    class CleanURLHandler(http.server.SimpleHTTPRequestHandler):
        """Handler that supports clean URLs (HTML rewriting)."""
        def do_GET(self):
            # Try .html extension if path has no extension and doesn't exist
            path = self.path.split('?')[0].split('#')[0]
            if '.' not in os.path.basename(path):
                html_path = os.path.join(os.getcwd(), path.lstrip('/') + '.html')
                if os.path.isfile(html_path):
                    self.path = path + '.html'
            super().do_GET()

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), CleanURLHandler) as httpd:
        click.echo(f"Serving at http://localhost:{port}")
        click.echo("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            click.echo("\nServer stopped.")


@cli.command()
@click.argument('collection')
@click.argument('title')
@click.option('--config', default='config.py', help='Config file path')
def new(collection: str, title: str, config: str):
    """Create a new content file."""
    config_path = Path(config).resolve()

    if not config_path.exists():
        click.echo(f"Config file not found: {config_path}", err=True)
        sys.exit(1)

    from .building import load_config
    from .parsing import slugify

    site_config = load_config(config_path)

    # Find collection config
    coll_config = None
    for c in site_config.collections:
        if c['name'] == collection:
            coll_config = c
            break

    if coll_config is None:
        click.echo(f"Unknown collection: {collection}", err=True)
        click.echo(f"Available: {', '.join(c['name'] for c in site_config.collections)}")
        sys.exit(1)

    # Generate filename
    slug = slugify(title)
    source_dir = config_path.parent / coll_config['source_dir']
    source_dir.mkdir(parents=True, exist_ok=True)

    # Use title as filename for dreams (they use spaces), slug for others
    if collection == 'dream':
        filename = f"{title}.md"
    else:
        filename = f"{slug}.md"

    filepath = source_dir / filename

    if filepath.exists():
        click.echo(f"File already exists: {filepath}", err=True)
        sys.exit(1)

    # Create content
    date = datetime.now().strftime('%Y-%m-%d')
    content = f"Title: {title}\nDate: {date}\n"

    if collection == 'dream':
        content += "Tags: \n"

    content += "\n"

    filepath.write_text(content, encoding='utf-8')
    click.echo(f"Created: {filepath}")


@cli.command()
@click.option('--port', default=8000, help='Port to serve on')
@click.option('--config', default='config.py', help='Config file path')
def watch(port: int, config: str):
    """Watch for changes and rebuild automatically, with dev server."""
    import threading
    import time
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    config_path = Path(config).resolve()

    if not config_path.exists():
        click.echo(f"Config file not found: {config_path}", err=True)
        sys.exit(1)

    from .building import load_config
    site_config = load_config(config_path)

    # Track rebuild state
    needs_rebuild = threading.Event()
    needs_rebuild.set()  # Initial build

    class RebuildHandler(FileSystemEventHandler):
        def __init__(self):
            self.last_event = 0

        def on_any_event(self, event):
            # Debounce events (500ms)
            now = time.time()
            if now - self.last_event < 0.5:
                return
            self.last_event = now

            # Ignore output directory, hidden files, pycache, and ivygen source
            path = event.src_path
            if any(x in path for x in ['output', '/.', '__pycache__', 'ivygen/']):
                return

            # Only rebuild for relevant file types
            if path.endswith(('.md', '.html', '.css', '.js')):
                click.echo(f"Change detected: {path}")
                needs_rebuild.set()

    def rebuild_loop():
        while True:
            needs_rebuild.wait()
            needs_rebuild.clear()
            click.echo("\nRebuilding...")
            try:
                # Re-run build with absolute config path
                ctx = click.Context(build)
                ctx.invoke(build, dev=True, config=str(config_path))
            except Exception as e:
                click.echo(f"Build error: {e}", err=True)

    # Start rebuild thread
    rebuild_thread = threading.Thread(target=rebuild_loop, daemon=True)
    rebuild_thread.start()

    # Set up file watcher
    observer = Observer()
    handler = RebuildHandler()

    # Watch content, theme, and config
    watch_paths = [
        site_config.content_dir,
        site_config.theme_dir,
        config_path.parent,
    ]

    for path in watch_paths:
        if path.exists():
            observer.schedule(handler, str(path), recursive=True)
            click.echo(f"Watching: {path}")

    observer.start()

    # Wait for initial build
    time.sleep(1)

    # Start server
    output_dir = site_config.output_dir
    os.chdir(output_dir)

    class CleanURLHandler(http.server.SimpleHTTPRequestHandler):
        """Handler that supports clean URLs (HTML rewriting)."""
        def do_GET(self):
            path = self.path.split('?')[0].split('#')[0]
            if '.' not in os.path.basename(path):
                html_path = os.path.join(os.getcwd(), path.lstrip('/') + '.html')
                if os.path.isfile(html_path):
                    self.path = path + '.html'
            super().do_GET()

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), CleanURLHandler) as httpd:
        url = f"http://localhost:{port}"
        click.echo(f"\nServing at {url}")
        click.echo("Watching for changes... Press Ctrl+C to stop.")

        import webbrowser
        webbrowser.open(url)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            click.echo("\nStopping...")
            observer.stop()

    observer.join()


@cli.command()
@click.option('--config', default='config.py', help='Config file path')
def clean(config: str):
    """Clean the output directory."""
    config_path = Path(config).resolve()

    if not config_path.exists():
        click.echo(f"Config file not found: {config_path}", err=True)
        sys.exit(1)

    from .building import load_config
    site_config = load_config(config_path)

    import shutil
    if site_config.output_dir.exists():
        shutil.rmtree(site_config.output_dir)
        click.echo(f"Cleaned: {site_config.output_dir}")
    else:
        click.echo("Output directory does not exist.")


def main():
    cli()


if __name__ == '__main__':
    main()
