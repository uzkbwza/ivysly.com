"""IvyGen configuration for ivysly.com"""

# Site metadata
SITE_NAME = 'ivysly.com'
SITE_URL = 'https://ivysly.com'
DEV_URL = ''  # Empty for file:// URLs, or 'http://localhost:8000'
AUTHOR = 'ivy sly'
TIMEZONE = 'America/Los_Angeles'

# Directories
CONTENT_DIR = 'content'
OUTPUT_DIR = 'output'
THEME_DIR = 'theme'
STATIC_DIRS = ['content/static']

# Navigation
NAVIGATION_LINKS = [
    ('games', 'games'),
    ('music', 'music'),
    ('blog', 'blog'),
    ('dreams', 'dream'),
    ('misc', 'misc'),
    ('about', 'about'),
]

# Collections
COLLECTIONS = [
    {
        'name': 'dream',
        'source_dir': 'content/dream',
        'item_template': 'dream.html',
        'list_template': 'dreamlog.html',
        'tag_template': 'tag.html',
        'tags_list_template': 'tags.html',
        'item_url': 'dream/{slug}.html',
        'list_url': 'dream.html',
        'tag_url': 'dream/tag/{slug}.html',
        'tags_list_url': 'dream/tags.html',
        'rss_enabled': True,
        'rss_url': 'feeds/dream.rss.xml',
        'sort_by': 'date',
        'sort_reverse': True,
        'optional_fields': {
            'tags': '',
        },
    },
    {
        'name': 'blog',
        'source_dir': 'content/blog',
        'item_template': 'blogpost.html',
        'list_template': 'blog.html',
        'tag_template': None,
        'item_url': 'blog/{slug}.html',
        'list_url': 'blog.html',
        'tag_url': None,
        'rss_enabled': True,
        'rss_url': 'feeds/blog.rss.xml',
        'sort_by': 'date',
        'sort_reverse': True,
        'optional_fields': {
            'comments': None,
            'status': 'published',
        },
    },
    {
        'name': 'games',
        'source_dir': 'content/games',
        'item_template': 'game.html',
        'list_template': 'gamelist.html',
        'tag_template': None,
        'item_url': 'games/{slug}.html',
        'list_url': 'games.html',
        'tag_url': None,
        'rss_enabled': True,
        'rss_url': 'feeds/games.rss.xml',
        'sort_by': 'date',
        'sort_reverse': True,
        'optional_fields': {
            'madewith': None,
            'steam': None,
            'itch': None,
            'windows': None,
            'linux': None,
            'mac': None,
            'rpi': None,
            'love': None,
            'lexaloffle': None,
            'discord': None,
            'oldversions': None,
            'image': None,
            'cover': None,
            'download': False,
            'link': False,
            'nondevcredit': False,
            'featured': False,
            'datetext': None,
            'description': None,
            'comments': None,
        },
    },
    {
        'name': 'patchnotes',
        'source_dir': 'content/patchnotes',
        'item_template': 'patchnotes.html',
        'list_template': None,  # No list page
        'tag_template': None,
        'item_url': 'hustle/patchnotes/{slug}.html',
        'list_url': None,
        'tag_url': None,
        'rss_enabled': True,
        'rss_url': 'feeds/hustle.rss.xml',
        'sort_by': 'date',
        'sort_reverse': True,
        'optional_fields': {
            'category': 'Hustle',
        },
    },
    {
        'name': 'reviews',
        'source_dir': 'content/reviews',
        'item_template': 'review.html',
        'list_template': 'reviewlist.html',
        'tag_template': None,
        'item_url': 'reviews/{slug}.html',
        'list_url': 'reviews.html',
        'tag_url': None,
        'rss_enabled': True,
        'rss_url': 'feeds/reviews.rss.xml',
        'sort_by': 'date',
        'sort_reverse': True,
        'optional_fields': {
            'cover': None,
            'banner': None,
            'released': None,
            'platform': None,
            'backloggd': None,
            'rating': None,
            'steam': None,
            'itch': None,
            'gog': None,
            'link': None,
            'comments': None,
            'description': None,
        },
    },
    {
        'name': 'misc',
        'source_dir': 'content/misc',
        'item_template': 'miscentry.html',
        'list_template': 'misc.html',
        'tag_template': None,
        'item_url': 'misc/{slug}.html',
        'list_url': 'misc.html',
        'tag_url': None,
        'rss_enabled': True,
        'rss_url': 'feeds/misc.rss.xml',
        'sort_by': 'sortorder',
        'sort_reverse': False,
        'optional_fields': {
            'sortorder': 100,
            'shorttitle': None,
            'summary': None,
        },
    },
]

# Pages (individual markdown files with explicit templates)
PAGES = {
    'about': {
        'source': 'content/pages/about.md',
        'template': 'about.html',
        'url': 'about.html',
    },
    'music': {
        'source': 'content/pages/music.md',
        'template': 'music.html',
        'url': 'music.html',
    },
}

# Template pages (Jinja templates rendered directly, no markdown source)
TEMPLATE_PAGES = {
    'home.html': 'index.html',
    'friends.html': 'misc/friends.html',
    'pixel-game-resolution-finder.html': 'misc/pixel-game-resolution-finder.html',
}

# RSS settings
RSS_ITEM_LIMIT = 100
