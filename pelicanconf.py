import os
print()
AUTHOR = 'ivy sly'
SITENAME = 'ivysly.com'
HTML_SITEURL = os.getcwd().replace("\\", "/") + "/output"
SITEHOME = HTML_SITEURL + "/index.html"
SITEURL = os.getcwd().replace("\\", "/") + "/output"


PATH = "content"

TIMEZONE = 'America/Los_Angeles'

DEFAULT_LANG = 'English'

THEME="theme"

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None
DELETE_OUTPUT_DIRECTORY = True
OUTPUT_RETENTION = ["static"]	
USE_FOLDER_AS_CATEGORY = True
RELATIVE_URLS = False

ARTICLE_URL = '{category}/{slug}.html'
ARTICLE_SAVE_AS = '{category}/{slug}.html'
TAG_SAVE_AS = 'tag/{slug}.html'

CATEGORY_URL = '{slug}.html'
CATEGORY_SAVE_AS = '{slug}.html'


PAGE_URL = '{slug}.html'
PAGE_SAVE_AS = '{slug}.html'

NAVIGATION_LINKS = [
    ("games", "games.html"),
    ("music", "music.html"),
    ("blog", "blog.html"),
    ("dreams", "dream.html"),
    ("misc", "misc.html"),
    ("about", "about.html"),
    ]

TEMPLATE_PAGES = {
    "home.html": "index.html",
    "friends.html": "misc/friends.html",
    }


DEFAULT_PAGINATION = False