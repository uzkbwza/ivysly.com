import os
import re
import discord
from discord.ext import commands
from datetime import datetime
import subprocess


intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Enable the Message Content Intent in your bot settings

bot = commands.Bot(command_prefix="!", intents=intents)

# Example command format:
# !dream Lights|house mansion
#
# Where "Lights" is the title, and "house mansion" are the tags.

def parse_dream_command(command_str):
    """
    Parse a command string of the form:
        !dream <title>|<tags>

    Example:
        command_str = "!dream Lights|house mansion"
        returns ("Lights", "house mansion")
    """
    pattern = r'^!dream\s+([^|]+)\|(.*)$'
    match = re.match(pattern, command_str.strip())
    if not match:
        return "", ""

    title = match.group(1).strip()
    tags = match.group(2).strip()

    # Capitalize the first letter of the title if desired
    # (Remove .capitalize() if you want to keep original casing.)
    title = title.title()

    return title, tags

def convert_dream(title, tags, content):
    """
    Convert dream text into a standardized format:
      Title: <title>
      Date: YYYY-MM-DD
      Tags: <comma-separated tags>

      <remaining dream text>
    """

    # 1. Extract the date line at the beginning of `content`.
    #    Looks for patterns like: 'Sat, 01 Feb 2025:'
    #    Then captures '01 Feb 2025'.
    date_pattern = r'^[A-Za-z]{3},?\s+(\d{1,2}\s+[A-Za-z]{3}\s+\d{4}):?'
    match = re.search(date_pattern, content, flags=re.MULTILINE)
    if not match:
        # If no date is found, default to empty string or handle differently
        dream_date = ""
    else:
        # 2. Convert '01 Feb 2025' to '2025-02-01'
        raw_date_str = match.group(1).strip()  # e.g. "01 Feb 2025"
        parsed_date = datetime.strptime(raw_date_str, "%d %b %Y")
        dream_date = parsed_date.strftime("%Y-%m-%d")

    # 3. Remove everything after (and including) '----'.
    #    For simplicity, we'll just split on '----' and keep the first part.
    content = content.split('----')[0]

    # 4. Remove the date line itself from the dream text.
    #    We can do this by substituting it out using the same pattern.
    content_cleaned = re.sub(date_pattern, '', content, flags=re.MULTILINE).strip()

    # 5. Convert the tags string into a list (assuming spaces separate individual tags).
    if isinstance(tags, str):
        tags_list = tags.split()
    else:
        tags_list = tags

    # 6. Construct the final output
    result = f"""Title: {title}
Date: {dream_date}
Tags: {", ".join(tags_list)}

{content_cleaned}
"""
    return result

def extract_dream_title(dream_text):
    """
    Extract the title from a formatted dream text which includes a line:
        Title: <title>
    Returns the title string if found, otherwise None.
    """
    pattern = r'^Title:\s*(.*)$'
    match = re.search(pattern, dream_text, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None

def deploy_dream(title, content):
    """
    Example deployment function that writes the content to a .md file
    and could optionally run a script (deploy.sh) afterwards.
    """
    current_dir = os.path.dirname(os.path.realpath(__file__))
    os.chdir(current_dir)

    # Make file in content/dream/title.md
    file_path = f"content/dream/{title}.md"
    with open(file_path, "w") as file:
        file.write(content)

    # Example: Using bash -c to run multiple commands, if needed.
    command = f"./deploy.sh"
    result = subprocess.run(["wsl", "bash", "-c", command],
                            capture_output=True,
                            text=True)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def dream(ctx):
    """
    Command usage example:
       !dream Lights|house mansion
    (And the user must reply to a message containing dream text.)
    """
    if ctx.message.reference:
        ref_msg = await ctx.message.channel.fetch_message(ctx.message.reference.message_id)
        # Attempt to parse title and tags from the command
        title, tags = parse_dream_command(ctx.message.content)
        if title and tags:
            # Convert dream text
            content = convert_dream(title, tags, ref_msg.content)
            await ctx.send(content)
        else:
            await ctx.send("Invalid command format. Use '!dream <title>|<tags>'.")
    else:
        await ctx.send("Please reply to a message containing the dream text and provide '!dream <title>|<tags>'.")

@bot.command()
async def send(ctx):
    """
    Example usage:
       !send
    Must be replying to a message containing the already converted dream text.
    """
    if not ctx.message.reference:
        return await ctx.send("Please reply to a message containing the dream text to send/deploy.")
    
    ref_msg = await ctx.message.channel.fetch_message(ctx.message.reference.message_id)
    title = extract_dream_title(ref_msg.content)
    if title:
        deploy_dream(title, ref_msg.content)
        await ctx.send(f"Dream '{title}' has been published to ivysly.com.")
    else:
        await ctx.send("No title found in the reference message.")

bot.run("REDACTED")