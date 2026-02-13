# This file is only used if you use `make publish` or
# explicitly specify it as your config file.

import os
import sys

sys.path.append(os.curdir)
from pelicanconf import *

# If your site is available via HTTPS, make sure SITEURL begins with https://
HTML_SITEURL = ""
SITEHOME = "/"
SITEURL = "https://ivysly.com"
RELATIVE_URLS = False

FEED_ALL_RSS = "feeds/all.rss.xml"
CATEGORY_FEED_RSS = "feeds/{slug}.rss.xml"

DELETE_OUTPUT_DIRECTORY = True

RELATIVE_URLS = False