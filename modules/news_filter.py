# news_filter.py
import re
from difflib import SequenceMatcher

from modules.news_config import (
    RE_ESTATE,
    RE_EXCLUDE,
    RE_MARKET_REQUIRED,
    STOPWORDS,
    LOC_ENTITIES,
    ORG_ENTITIES,
)
