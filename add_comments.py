#!/usr/bin/env python3
"""Find uncommented games/blogs and add Bluesky comment links."""

import argparse
import re
from pathlib import Path


def parse_frontmatter(text: str) -> tuple[dict, int]:
    """Parse frontmatter and return (meta dict, body start line index)."""
    lines = text.split('\n')
    meta = {}
    body_start = 0

    for i, line in enumerate(lines):
        if not line.strip():
            body_start = i
            break
        if ':' in line:
            key, _, value = line.partition(':')
            meta[key.strip().lower()] = value.strip()

    return meta, body_start


def extract_post_id(url: str) -> str | None:
    """Extract post ID from Bluesky URL."""
    # Match patterns like:
    # https://bsky.app/profile/ivysly.com/post/3lyuf3rxi322r
    # https://bsky.app/profile/did:plc:.../post/3lyuf3rxi322r
    match = re.search(r'/post/([a-zA-Z0-9]+)/?$', url.strip())
    if match:
        return match.group(1)
    return None


def set_comments_field(filepath: Path, post_id: str) -> bool:
    """Add or update Comments field in frontmatter."""
    text = filepath.read_text(encoding='utf-8')
    lines = text.split('\n')

    # Check if Comments field already exists
    comments_line = None
    for i, line in enumerate(lines):
        if not line.strip():
            break
        if line.lower().startswith('comments:'):
            comments_line = i
            break

    if comments_line is not None:
        # Update existing
        lines[comments_line] = f'Comments: {post_id}'
    else:
        # Find where frontmatter ends (first blank line)
        insert_at = 0
        for i, line in enumerate(lines):
            if not line.strip():
                insert_at = i
                break
            insert_at = i + 1
        # Insert Comments field before the blank line
        lines.insert(insert_at, f'Comments: {post_id}')

    filepath.write_text('\n'.join(lines), encoding='utf-8')
    return True


def find_content(content_dir: Path, folders: list[str], only_uncommented: bool = True) -> list[Path]:
    """Find content files."""
    found = []

    for folder in folders:
        folder_path = content_dir / folder
        if not folder_path.exists():
            continue

        for md_file in folder_path.glob('*.md'):
            text = md_file.read_text(encoding='utf-8')
            meta, _ = parse_frontmatter(text)

            # Skip drafts
            if meta.get('status') == 'draft':
                continue

            if only_uncommented:
                if 'comments' not in meta or not meta['comments']:
                    found.append(md_file)
            else:
                found.append(md_file)

    return found


def main():
    parser = argparse.ArgumentParser(description='Add/update Bluesky comment links')
    parser.add_argument('--all', '-a', action='store_true',
                        help='Show all items, not just uncommented ones')
    args = parser.parse_args()

    base_dir = Path(__file__).parent
    content_dir = base_dir / 'content'

    # Find content
    items = find_content(content_dir, ['blog', 'games', 'reviews'], only_uncommented=not args.all)

    if not items:
        print("No items found!")
        return

    mode = "all" if args.all else "uncommented"
    print(f"Found {len(items)} {mode} items:\n")

    for filepath in items:
        text = filepath.read_text(encoding='utf-8')
        meta, _ = parse_frontmatter(text)
        title = meta.get('title', filepath.stem)
        category = filepath.parent.name
        current = meta.get('comments', '')

        print(f"[{category}] {title}")
        print(f"  File: {filepath.name}")
        if current:
            print(f"  Current: {current}")
        print()

        while True:
            prompt = "  Paste Bluesky URL (enter to keep" if current else "  Paste Bluesky URL (enter to skip"
            user_input = input(f"{prompt}, 'q' to quit): ").strip()

            if user_input.lower() == 'q':
                print("\nQuitting.")
                return

            if not user_input:
                print("  Kept.\n" if current else "  Skipped.\n")
                break

            post_id = extract_post_id(user_input)

            if post_id:
                set_comments_field(filepath, post_id)
                print(f"  Set: Comments: {post_id}\n")
                break
            else:
                print("  Could not extract post ID. Try again.")

    print("Done!")


if __name__ == '__main__':
    main()
