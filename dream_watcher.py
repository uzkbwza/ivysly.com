import os
import re
import discord
from discord.ext import commands
from datetime import datetime
import subprocess
from pathlib import Path

from slugify import slugify
from scrape_backloggd import (
    fetch_page, parse_review_body, fetch_game_page_info,
    download_cover, download_banner, parse_date,
    CONTENT_DIR as REVIEWS_CONTENT_DIR,
    IMAGES_DIR as REVIEWS_IMAGES_DIR,
    BASE_URL,
)

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

###############################################################################
# CORE HELPERS
###############################################################################

def parse_dream_command(command_str):
    """
    Parse a command string of the form:
        !dream <title>|<tags>
    Example:
        "!dream Lights|house mansion" -> ("Lights", "house mansion")
    """
    pattern = r'^!dream\s+([^|]+)\|(.*)$'
    match = re.match(pattern, command_str.strip())
    if not match:
        return "", ""
    title = match.group(1).strip()
    tags = match.group(2).strip()

    # Capitalize the first letter of the title if desired
    title = title.title()
    return title, tags


def parse_blog_command(command_str):
    """
    Parse a command string of the form:
        !blog <title>
    Example:
        "!blog My First Post" -> "My First Post"
    """
    pattern = r'^!blog\s+(.*)$'
    match = re.match(pattern, command_str.strip())
    if not match:
        return ""
    title = match.group(1).strip()

    # Capitalize the first letter of the title if desired
    title = title.title()
    return title


def convert_dream(title, tags, content):
    """
    Convert dream text into a standardized format:
      Title: <title>
      Date: YYYY-MM-DD
      Tags: <comma-separated tags>

      <remaining dream text>
    """
    date_pattern = r'^[A-Za-z]{3},?\s+(\d{1,2}\s+[A-Za-z]{3}\s+\d{4}):?'
    match = re.search(date_pattern, content, flags=re.MULTILINE)
    if not match:
        dream_date = ""
    else:
        raw_date_str = match.group(1).strip()  # e.g. "01 Feb 2025"
        parsed_date = datetime.strptime(raw_date_str, "%d %b %Y")
        dream_date = parsed_date.strftime("%Y-%m-%d")

    # Remove everything after '----' (if present).
    content = content.split('----')[0]

    # Remove the date line itself.
    content_cleaned = re.sub(date_pattern, '', content, flags=re.MULTILINE).strip()

    # Convert the tags string into a list (assuming spaces separate individual tags).
    if isinstance(tags, str):
        tags_list = tags.split()
    else:
        tags_list = tags

    result = f"""Title: {title}
Date: {dream_date}
Tags: {", ".join(tags_list)}

{content_cleaned}
"""
    return result


def convert_blog(title, content):
    """
    Convert blog text into a standardized format:
      Title: <title>
      Date: YYYY-MM-DD

      <remaining blog text>
    """
    date_pattern = r'^[A-Za-z]{3},?\s+(\d{1,2}\s+[A-Za-z]{3}\s+\d{4}):?'
    match = re.search(date_pattern, content, flags=re.MULTILINE)
    if not match:
        dream_date = ""
    else:
        raw_date_str = match.group(1).strip()  # e.g. "01 Feb 2025"
        parsed_date = datetime.strptime(raw_date_str, "%d %b %Y")
        dream_date = parsed_date.strftime("%Y-%m-%d")

    # Remove everything after '----' (if present).
    content = content.split('----')[0]

    # Remove the date line itself.
    content_cleaned = re.sub(date_pattern, '', content, flags=re.MULTILINE).strip()

    result = f"""Title: {title}
Date: {dream_date}

{content_cleaned}
"""
    return result


def extract_title(text):
    """
    Extract the title from a formatted text which includes a line:
        Title: <title>
    """
    pattern = r'^Title:\s*(.*)$'
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1).strip() if match else None


def deploy_post(post_type, title, content, overwrite=False):
    """
    Writes the content to content/<post_type>/<title>.md.
    If overwrite=False, raises FileExistsError if the file already exists.
    """
    current_dir = os.path.dirname(os.path.realpath(__file__))
    os.chdir(current_dir)

    file_path = f"content/{post_type}/{title.replace(' ', '-')}.md"
    if not overwrite and os.path.exists(file_path):
        raise FileExistsError(f"The file '{file_path}' already exists.")

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)

    # Deploy to server
    subprocess.run(["./deploy.sh"], capture_output=True, text=True)


###############################################################################
# TAG ADD/REMOVE CORE LOGIC (NO DEPLOY INSIDE THESE FUNCTIONS)
###############################################################################

def add_tags_to_one_dream(title, new_tags):
    """
    Opens 'content/dream/<title>.md', finds the 'Tags:' line, merges `new_tags`,
    and saves.
    """
    current_dir = os.path.dirname(os.path.realpath(__file__))
    os.chdir(current_dir)

    file_path = f"content/dream/{title.replace(' ', '-')}.md"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"No dream file found for '{title}'.")

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Find the 'Tags:' line
    tags_line_idx = None
    for i, line in enumerate(lines):
        if line.startswith("Tags:"):
            tags_line_idx = i
            break
    if tags_line_idx is None:
        raise ValueError(f"'Tags:' line not found in {file_path}.")

    # Parse existing tags
    existing_tags_str = lines[tags_line_idx][len("Tags:"):].strip()
    existing_tags = [t.strip() for t in existing_tags_str.split(",") if t.strip()]

    # Merge new tags and remove duplicates
    combined_tags = set(existing_tags + list(new_tags))
    combined_tags_sorted = sorted(combined_tags)

    # Rewrite
    new_tags_str = ", ".join(combined_tags_sorted)
    lines[tags_line_idx] = f"Tags: {new_tags_str}\n"

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def remove_tags_from_one_dream(title, remove_tags):
    """
    Removes specified tags from a single dream file <title>.md.
    Returns True if at least one tag was actually removed; otherwise False.
    """
    current_dir = os.path.dirname(os.path.realpath(__file__))
    os.chdir(current_dir)

    file_path = f"content/dream/{title.replace(' ', '-')}.md"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"No dream file found for '{title}'.")

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Find 'Tags:' line
    tags_line_idx = None
    for i, line in enumerate(lines):
        if line.startswith("Tags:"):
            tags_line_idx = i
            break
    if tags_line_idx is None:
        raise ValueError(f"'Tags:' line not found in {file_path}.")

    # Parse existing tags
    existing_tags_str = lines[tags_line_idx][len("Tags:"):].strip()
    existing_tags = [t.strip() for t in existing_tags_str.split(",") if t.strip()]

    old_count = len(existing_tags)
    # Remove the unwanted tags
    new_tag_set = set(existing_tags) - set(remove_tags)
    new_tags_sorted = sorted(new_tag_set)
    new_tags_str = ", ".join(new_tags_sorted)

    lines[tags_line_idx] = f"Tags: {new_tags_str}\n"

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    new_count = len(new_tags_sorted)
    return new_count < old_count  # True if we actually removed something


def remove_tags_from_all_dreams(remove_tags):
    """
    Loops over ALL .md files in content/dream/ to remove the given tags.
    Returns a list of dream titles that actually had tags removed.
    """
    current_dir = os.path.dirname(os.path.realpath(__file__))
    os.chdir(current_dir)

    dream_dir = os.path.join(current_dir, "content", "dream")
    if not os.path.isdir(dream_dir):
        raise FileNotFoundError("The 'content/dream' directory does not exist.")

    md_files = [f for f in os.listdir(dream_dir) if f.endswith(".md")]

    titles_changed = []

    for md_file in md_files:
        file_path = os.path.join(dream_dir, md_file)
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # We also want to read the actual Title: line, to show a friendlier name.
        # We'll default to the filename (minus .md) if no Title line is found.
        dream_title_in_file = None
        tags_line_idx = None

        for i, line in enumerate(lines):
            if line.startswith("Title:"):
                dream_title_in_file = line[len("Title:"):].strip()
            if line.startswith("Tags:"):
                tags_line_idx = i

        # If we didn't find a dream title, use the filename (minus .md)
        if not dream_title_in_file:
            dream_title_in_file = md_file[:-3]  # remove .md

        if tags_line_idx is None:
            # no Tags: line in this file
            continue

        existing_tags_str = lines[tags_line_idx][len("Tags:"):].strip()
        existing_tags = [t.strip() for t in existing_tags_str.split(",") if t.strip()]

        old_count = len(existing_tags)
        # Subtract out the tags being removed
        new_tag_set = set(existing_tags) - set(remove_tags)
        new_tags_sorted = sorted(new_tag_set)
        new_tags_str = ", ".join(new_tags_sorted)

        # Only write back if there's actually a difference (some tags were removed)
        if len(new_tags_sorted) < old_count:
            lines[tags_line_idx] = f"Tags: {new_tags_str}\n"
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)

            # Record that we changed this dream
            titles_changed.append(dream_title_in_file)

    return titles_changed


###############################################################################
# PARSING MULTIPLE TITLES + TAGS
###############################################################################

def parse_titles_and_tags(input_str):
    """
    Extract zero or more quoted titles, then interpret the rest as tags.

    e.g.:
      input_str = '"Title One" "Second Title" tag1 tag2'
      -> titles = ["Title One", "Second Title"]
         tags   = ["tag1", "tag2"]

    If zero titles are found, `titles` will be an empty list.
    """
    # Find all quoted strings
    pattern = r'"([^"]+)"'
    titles = re.findall(pattern, input_str)

    # Remove those quoted parts from the string to get the leftover (tags).
    remainder = re.sub(r'"[^"]+"', '', input_str).strip()
    tags = remainder.split()

    return titles, tags


###############################################################################
# DISCORD EVENTS & COMMANDS
###############################################################################

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.command()
async def dream(ctx):
    """
    Usage:
       !dream Lights|house mansion
    Then reply to a message that has the raw dream text.
    """
    if ctx.message.reference:
        ref_msg = await ctx.message.channel.fetch_message(ctx.message.reference.message_id)
        title, tags = parse_dream_command(ctx.message.content)
        if title and tags:
            content = convert_dream(title, tags, ref_msg.content)
            await ctx.send(content)
        else:
            await ctx.send("Invalid command format. Use '!dream <title>|<tags>'.")
    else:
        await ctx.send("Please reply to a message containing the dream text and provide '!dream <title>|<tags>'.")


@bot.command()
async def blog(ctx):
    """
    Usage:
       !blog My First Post
    Then reply to a message that has the raw blog text.
    """
    if ctx.message.reference:
        ref_msg = await ctx.message.channel.fetch_message(ctx.message.reference.message_id)
        title = parse_blog_command(ctx.message.content)
        if title:
            content = convert_blog(title, ref_msg.content)
            await ctx.send(content)
        else:
            await ctx.send("Invalid command format. Use '!blog <title>'.")
    else:
        await ctx.send("Please reply to a message containing the blog text and provide '!blog <title>'.")


@bot.command()
async def send(ctx, post_type: str = None):
    """
    Must be replying to a message containing the formatted text.
    Usage: !send dream  or  !send blog
    """
    if post_type not in ("dream", "blog"):
        return await ctx.send("Please specify a type: `!send dream` or `!send blog`.")

    if not ctx.message.reference:
        return await ctx.send("Please reply to a message containing the text to publish.")

    ref_msg = await ctx.message.channel.fetch_message(ctx.message.reference.message_id)
    content = ref_msg.content
    title = extract_title(content)

    if title:
        try:
            deploy_post(post_type, title, content, overwrite=False)
            await ctx.send(f"'{title}' has been published as {post_type} to ivysly.com.")
        except FileExistsError:
            await ctx.send(
                f"A post with the title '{title}' already exists. "
                f"Use `!overwrite {post_type}` if you wish to overwrite the existing file."
            )
    else:
        await ctx.send("No title found in the referenced message.")


@bot.command()
async def overwrite(ctx, post_type: str = None):
    """
    Overwrites an existing post file if it exists.
    Usage: !overwrite dream  or  !overwrite blog
    """
    if post_type not in ("dream", "blog"):
        return await ctx.send("Please specify a type: `!overwrite dream` or `!overwrite blog`.")

    if not ctx.message.reference:
        return await ctx.send("Please reply to a message containing the text to overwrite.")

    ref_msg = await ctx.message.channel.fetch_message(ctx.message.reference.message_id)
    content = ref_msg.content
    title = extract_title(content)

    if title:
        try:
            deploy_post(post_type, title, content, overwrite=True)
            await ctx.send(f"'{title}' has been overwritten and published as {post_type} to ivysly.com.")
        except Exception as e:
            await ctx.send(f"An error occurred while overwriting: {e}")
    else:
        await ctx.send("No title found in the referenced message.")


###############################################################################
# ADDTAGS (MULTIPLE TITLES)
###############################################################################
@bot.command()
async def addtags(ctx, *, input_str: str):
    """
    Usage:
       !addtags "Title One" "Title Two" tag1 tag2 ...
    This adds the same tags to all specified dream titles.
    """
    titles, new_tags = parse_titles_and_tags(input_str)

    if not titles:
        return await ctx.send(
            "Please provide at least one quoted title. E.g.\n"
            '!addtags "My Dream Title" tag1 tag2'
        )
    if not new_tags:
        return await ctx.send("Please provide at least one tag to add.")

    errors = []
    for t in titles:
        try:
            add_tags_to_one_dream(t, new_tags)
        except Exception as e:
            errors.append(f"- Title '{t}': {str(e)}")

    # Single deploy after updating all specified dreams
    subprocess.run(["./deploy.sh"], capture_output=True, text=True)

    if errors:
        err_msg = "\n".join(errors)
        await ctx.send(
            f"Finished adding tags to some titles, but encountered errors:\n{err_msg}"
        )
    else:
        await ctx.send(
            f"Tags {new_tags} have been added to: {', '.join(titles)}"
        )


###############################################################################
# REMOVETAGS (MULTIPLE TITLES OR ALL, WITH REPORTING)
###############################################################################
@bot.command()
async def removetags(ctx, *, input_str: str):
    """
    Usage:
      !removetags "Title One" "Title Two" oldtag1 oldtag2 ...
        -> removes oldtag1, oldtag2, etc. from each listed dream

      !removetags oldtag1 oldtag2 ...
        -> removes those tags from ALL dream entries (no quotes),
           and lists which dream(s) actually changed.

    Examples:
      !removetags "Spooky House" "Another Dream" weird useless
      !removetags oldtag1 oldtag2
    """
    titles, remove_tags = parse_titles_and_tags(input_str)

    if not remove_tags:
        return await ctx.send("Please specify at least one tag to remove.")

    if titles:
        # Remove tags from each listed title
        errors = []
        changed_titles = []
        for t in titles:
            try:
                removed_any = remove_tags_from_one_dream(t, remove_tags)
                if removed_any:
                    changed_titles.append(t)
            except Exception as e:
                errors.append(f"- Title '{t}': {str(e)}")

        # Single deploy after updating all specified dreams
        subprocess.run(["./deploy.sh"], capture_output=True, text=True)

        # Build success message
        success_msg = ""
        if changed_titles:
            success_msg = f"Tags {remove_tags} have been removed from: {', '.join(changed_titles)}"
        else:
            success_msg = f"No tags were removed (none of the listed dreams had any of {remove_tags})."

        if errors:
            err_msg = "\n".join(errors)
            await ctx.send(
                f"{success_msg}\n\nHowever, some errors occurred:\n{err_msg}"
            )
        else:
            await ctx.send(success_msg)

    else:
        # No quoted titles => remove from ALL dream entries
        try:
            changed_titles = remove_tags_from_all_dreams(remove_tags)

            # Deploy once for the global update
            subprocess.run(["./deploy.sh"], capture_output=True, text=True)

            if changed_titles:
                await ctx.send(
                    f"Tags {remove_tags} have been removed from the following dreams:\n"
                    + "\n".join(f"- {title}" for title in changed_titles)
                )
            else:
                await ctx.send(
                    f"No tags were removed (no dream contained any of {remove_tags})."
                )

        except Exception as e:
            await ctx.send(f"An error occurred while removing from all: {e}")


###############################################################################
# REVIEW COMMAND
###############################################################################

def detect_store_type(url):
    """Detect what kind of store link a URL is."""
    url_lower = url.lower()
    if "store.steampowered.com" in url_lower or "steampowered.com" in url_lower:
        return "steam"
    if "itch.io" in url_lower:
        return "itch"
    if "gog.com" in url_lower:
        return "gog"
    return "link"


def scrape_review_from_backloggd(review_url):
    """Scrape a single review from Backloggd and return its data.

    Returns a dict with keys: title, slug, date, year, review_text,
    cover_url, game_url, backloggd_url.
    Raises ValueError if critical data is missing, with a message
    describing what couldn't be found.
    """
    soup = fetch_page(review_url)
    missing = []

    # Game title
    title = None
    game_url = None
    for a in soup.select('a[href*="/games/"]'):
        href = a.get("href", "")
        if "/games/lib/" not in href and a.get_text(strip=True):
            title = a.get_text(strip=True)
            game_url = BASE_URL + href if href.startswith("/") else href
            break
    if not title:
        missing.append("title (could not find game link on page)")

    # Date
    time_el = soup.select_one("time[datetime]")
    date_str = parse_date(time_el["datetime"]) if time_el else None
    if not date_str:
        missing.append("date")

    # Release date from game page
    released = None
    if game_url:
        try:
            _, released = fetch_game_page_info(game_url)
        except Exception:
            pass

    # Cover image
    cover_url = None
    cover_img = soup.select_one('img[src*="images.igdb.com"]')
    if cover_img:
        cover_url = cover_img["src"]

    # Review text
    card_text = soup.select_one(".review-body .card-text")
    review_text = parse_review_body(card_text) if card_text else None
    if not review_text:
        missing.append("review text")

    if missing:
        raise ValueError(
            "Could not scrape the following from Backloggd: "
            + ", ".join(missing)
            + ". Provide them as fallback args."
        )

    slug = slugify(title)
    return {
        "title": title,
        "slug": slug,
        "date": date_str,
        "released": released,
        "review_text": review_text,
        "cover_url": cover_url,
        "game_url": game_url,
        "backloggd_url": review_url,
    }


def build_review_markdown(data, store_links):
    """Build the markdown content string for a review.

    data: dict from scrape_review_from_backloggd
    store_links: dict like {"steam": "https://...", "itch": "https://..."}
    """
    lines = [f"Title: {data['title']}"]
    lines.append(f"Date: {data['date']}")
    lines.append(f"Slug: {data['slug']}")

    if data.get("cover_path"):
        lines.append(f"Cover: ./{data['cover_path']}")
    if data.get("banner_path"):
        lines.append(f"Banner: ./{data['banner_path']}")
    if data.get("released"):
        lines.append(f"Released: {data['released']}")

    lines.append(f"Backloggd: {data['backloggd_url']}")

    for key in ("steam", "itch", "gog", "link"):
        if key in store_links:
            lines.append(f"{key.capitalize()}: {store_links[key]}")

    lines.append("Comments:")
    lines.append("")
    lines.append(data["review_text"])
    lines.append("")
    return "\n".join(lines)


@bot.command()
async def review(ctx, *, args: str = ""):
    """
    Scrape a review from Backloggd and publish it.

    Usage:
      !review <backloggd_review_url> <game_store_url> [year=YYYY] [title=Name]

    The Backloggd URL is required. A store link (Steam/itch/GOG/other) is required.
    Optional fallback args if Backloggd is missing data:
      released=14 Feb 2024
      title=Game Name Here

    Examples:
      !review https://backloggd.com/u/ivysly/review/123456/ https://store.steampowered.com/app/12345/Game/
      !review https://backloggd.com/u/ivysly/review/123456/ https://example.itch.io/game released=20 Mar 2020
      !review https://backloggd.com/u/ivysly/review/123456/ https://store.steampowered.com/app/12345/Game/ title=Custom Title released=26 Mar 1998
    """
    if not args:
        return await ctx.send(
            "Usage: `!review <backloggd_url> <store_url> [released=DD Mon YYYY] [title=Name]`\n"
            "Both a Backloggd review URL and a store link are required."
        )

    # Parse args: URLs are tokens that start with http, key=value pairs are fallbacks
    tokens = args.split()
    urls = []
    fallbacks = {}
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if "=" in token and not token.startswith("http"):
            key, _, val = token.partition("=")
            # Value might span multiple tokens (e.g. title=Tomb Raider)
            # Collect until next key=val or URL
            parts = [val]
            while i + 1 < len(tokens) and "=" not in tokens[i + 1] and not tokens[i + 1].startswith("http"):
                i += 1
                parts.append(tokens[i])
            fallbacks[key.lower()] = " ".join(parts)
        elif token.startswith("http"):
            urls.append(token)
        i += 1

    # Identify backloggd URL and store URL
    backloggd_url = None
    store_url = None
    for u in urls:
        if "backloggd.com" in u:
            backloggd_url = u
        else:
            store_url = u

    if not backloggd_url:
        return await ctx.send("Error: No Backloggd review URL provided.")
    if not store_url:
        return await ctx.send("Error: A game store link is required (Steam, itch.io, GOG, or website).")

    store_type = detect_store_type(store_url)
    store_links = {store_type: store_url}

    await ctx.send(f"Scraping review from Backloggd...")

    # Scrape
    try:
        data = scrape_review_from_backloggd(backloggd_url)
    except ValueError as e:
        return await ctx.send(f"Error: {e}")
    except Exception as e:
        return await ctx.send(f"Error scraping Backloggd: {e}")

    # Apply fallbacks
    if "title" in fallbacks:
        data["title"] = fallbacks["title"]
        data["slug"] = slugify(fallbacks["title"])
    if "released" in fallbacks:
        data["released"] = fallbacks["released"]

    if not data.get("released"):
        return await ctx.send(
            f"Error: Could not find release date for **{data['title']}** on Backloggd. "
            "Re-run with `released=DD Mon YYYY` to provide it."
        )

    # Check if review already exists
    filepath = REVIEWS_CONTENT_DIR / f"{data['slug']}.md"
    if filepath.exists():
        return await ctx.send(
            f"Error: A review for **{data['title']}** already exists at `{filepath.name}`. "
            "Delete it first or edit it manually."
        )

    # Download cover
    REVIEWS_CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    REVIEWS_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    cover_path = None
    if data.get("cover_url"):
        try:
            cover_path = download_cover(data["cover_url"], data["slug"])
        except Exception as e:
            await ctx.send(f"Warning: Failed to download cover: {e}")
    else:
        await ctx.send("Warning: No cover image found on Backloggd.")
    data["cover_path"] = cover_path

    # Download banner (screenshot from game page)
    banner_path = None
    if data.get("game_url"):
        try:
            screenshot_url, _ = fetch_game_page_info(data["game_url"])
            if screenshot_url:
                banner_path = download_banner(screenshot_url, data["slug"])
            else:
                await ctx.send("Warning: No screenshot found for banner image.")
        except Exception as e:
            await ctx.send(f"Warning: Failed to download banner: {e}")
    data["banner_path"] = banner_path

    # Generate markdown
    md_content = build_review_markdown(data, store_links)
    filepath.write_text(md_content, encoding="utf-8")

    # Deploy
    current_dir = os.path.dirname(os.path.realpath(__file__))
    os.chdir(current_dir)
    subprocess.run(["./deploy.sh"], capture_output=True, text=True)

    await ctx.send(
        f"Published review for **{data['title']}** ({data.get('released', '?')}) to ivysly.com!\n"
        f"<https://ivysly.com/reviews/{data['slug']}.html>"
    )


bot.run("REDACTED")