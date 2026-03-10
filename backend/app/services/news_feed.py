"""
Real-time News Feed Integration
Fetches news articles from RSS feeds and news APIs to seed simulations with real-world context.
Supports multiple news sources with topic-based filtering.
"""

import json
import re
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError

from ..utils.logger import get_logger

logger = get_logger('mirofish.news_feed')


# Curated list of public RSS feeds by region/category
RSS_FEEDS = {
    "india": {
        "general": [
            {"name": "Times of India", "url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"},
            {"name": "NDTV", "url": "https://feeds.feedburner.com/ndtvnews-top-stories"},
            {"name": "The Hindu", "url": "https://www.thehindu.com/news/national/feeder/default.rss"},
        ],
        "tech": [
            {"name": "YourStory", "url": "https://yourstory.com/rss"},
        ],
        "business": [
            {"name": "Economic Times", "url": "https://economictimes.indiatimes.com/rssfeedstopstories.cms"},
            {"name": "Mint", "url": "https://www.livemint.com/rss/news"},
        ]
    },
    "us": {
        "general": [
            {"name": "Reuters", "url": "https://feeds.reuters.com/reuters/topNews"},
            {"name": "AP News", "url": "https://rsshub.app/apnews/topics/apf-topnews"},
        ],
        "tech": [
            {"name": "TechCrunch", "url": "https://techcrunch.com/feed/"},
            {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index"},
        ],
        "business": [
            {"name": "CNBC", "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"},
        ]
    },
    "global": {
        "general": [
            {"name": "BBC World", "url": "http://feeds.bbci.co.uk/news/world/rss.xml"},
            {"name": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml"},
        ],
        "tech": [
            {"name": "Hacker News", "url": "https://hnrss.org/frontpage"},
        ]
    }
}


@dataclass
class NewsArticle:
    """A news article from an RSS feed"""
    title: str
    description: str
    source: str
    url: str
    published: Optional[datetime] = None
    category: str = ""
    region: str = ""
    relevance_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary"""
        return {
            "title": self.title,
            "description": self.description,
            "source": self.source,
            "url": self.url,
            "published": self.published.isoformat() if self.published else None,
            "category": self.category,
            "region": self.region,
            "relevance_score": self.relevance_score,
        }


@dataclass
class NewsFeedConfig:
    """Configuration for news feed integration"""
    regions: List[str] = field(default_factory=lambda: ["india", "global"])
    categories: List[str] = field(default_factory=lambda: ["general"])
    keywords: List[str] = field(default_factory=list)
    max_articles: int = 10
    max_age_hours: int = 48  # Only fetch articles from last N hours


class NewsFeedService:
    """Fetches and filters news for simulation seeding"""

    USER_AGENT = "SocialSwarm/1.0 (Research Tool)"
    TIMEOUT = 10  # seconds

    def fetch_articles(self, config: NewsFeedConfig) -> List[NewsArticle]:
        """Fetch articles from configured RSS feeds"""
        articles = []

        for region in config.regions:
            if region not in RSS_FEEDS:
                continue
            for category in config.categories:
                if category not in RSS_FEEDS[region]:
                    continue
                for feed_info in RSS_FEEDS[region][category]:
                    try:
                        feed_articles = self._parse_rss(
                            feed_info["url"],
                            feed_info["name"],
                            region,
                            category
                        )
                        articles.extend(feed_articles)
                    except Exception as e:
                        logger.warning(f"Failed to fetch {feed_info['name']}: {e}")

        # Filter by age
        if config.max_age_hours:
            cutoff = datetime.now() - timedelta(hours=config.max_age_hours)
            articles = [
                a for a in articles
                if a.published is None or a.published.replace(tzinfo=None) >= cutoff
            ]

        # Filter by keywords if specified
        if config.keywords:
            articles = self._filter_by_keywords(articles, config.keywords)

        # Sort by relevance then recency
        articles.sort(key=lambda a: (a.relevance_score, a.published or datetime.min), reverse=True)

        return articles[:config.max_articles]

    def to_simulation_events(self, articles: List[NewsArticle], agent_ids: List[int] = None) -> List[Dict[str, Any]]:
        """Convert news articles to simulation initial posts / scheduled events"""
        events = []
        for i, article in enumerate(articles):
            post_content = f"{article.title}\n\n{article.description}"
            if article.url:
                post_content += f"\n\nSource: {article.source}"

            event = {
                "content": post_content,
                "source_url": article.url,
                "source_name": article.source,
                "region": article.region,
                "category": article.category,
            }

            # Assign to a specific agent if IDs provided
            if agent_ids:
                event["poster_agent_id"] = agent_ids[i % len(agent_ids)]

            events.append(event)

        return events

    def _parse_rss(self, url: str, source_name: str, region: str, category: str) -> List[NewsArticle]:
        """Parse an RSS feed and return articles"""
        req = Request(url, headers={"User-Agent": self.USER_AGENT})
        with urlopen(req, timeout=self.TIMEOUT) as response:
            content = response.read()

        root = self._safe_parse_xml(content)
        articles = []

        # Handle both RSS 2.0 and Atom formats
        # RSS 2.0
        for item in root.findall('.//item'):
            title = self._get_text(item, 'title')
            description = self._get_text(item, 'description')
            link = self._get_text(item, 'link')
            pub_date = self._parse_date(self._get_text(item, 'pubDate'))

            if title:
                # Clean HTML from description
                description = re.sub(r'<[^>]+>', '', description or '')
                description = description[:500]  # Truncate

                articles.append(NewsArticle(
                    title=title.strip(),
                    description=description.strip(),
                    source=source_name,
                    url=link or "",
                    published=pub_date,
                    category=category,
                    region=region
                ))

        # Atom format
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        for entry in root.findall('.//atom:entry', ns):
            title = self._get_text(entry, 'atom:title', ns)
            summary = self._get_text(entry, 'atom:summary', ns) or self._get_text(entry, 'atom:content', ns)
            link_elem = entry.find('atom:link', ns)
            link = link_elem.get('href', '') if link_elem is not None else ''
            pub_date = self._parse_date(
                self._get_text(entry, 'atom:published', ns) or self._get_text(entry, 'atom:updated', ns)
            )

            if title:
                summary = re.sub(r'<[^>]+>', '', summary or '')[:500]
                articles.append(NewsArticle(
                    title=title.strip(),
                    description=summary.strip(),
                    source=source_name,
                    url=link,
                    published=pub_date,
                    category=category,
                    region=region
                ))

        return articles

    def _safe_parse_xml(self, content: bytes) -> ET.Element:
        """Safely parse XML content, rejecting documents with DOCTYPE/ENTITY declarations
        to prevent XXE (XML External Entity) attacks.

        While Python's stdlib ElementTree does not process external entities by default,
        this explicit check provides defense-in-depth against potential entity expansion
        attacks (e.g., billion laughs) and future parser changes.
        """
        try:
            text = content.decode('utf-8', errors='replace')
        except Exception:
            text = content.decode('latin-1')

        # Reject XML with DOCTYPE or ENTITY declarations (case-insensitive)
        if re.search(r'<!DOCTYPE\b', text, re.IGNORECASE) or re.search(r'<!ENTITY\b', text, re.IGNORECASE):
            raise ValueError(
                "XML content contains DOCTYPE or ENTITY declarations, which are rejected for security reasons."
            )

        return ET.fromstring(content)

    def _get_text(self, element, tag, ns=None):
        """Get text content of a child element"""
        child = element.find(tag, ns) if ns else element.find(tag)
        return child.text if child is not None and child.text else ""

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats from RSS feeds"""
        if not date_str:
            return None
        formats = [
            "%a, %d %b %Y %H:%M:%S %z",    # RFC 822
            "%a, %d %b %Y %H:%M:%S %Z",
            "%Y-%m-%dT%H:%M:%S%z",          # ISO 8601
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        return None

    def _filter_by_keywords(self, articles: List[NewsArticle], keywords: List[str]) -> List[NewsArticle]:
        """Filter and score articles by keyword relevance"""
        filtered = []
        keywords_lower = [k.lower() for k in keywords]

        for article in articles:
            text = f"{article.title} {article.description}".lower()
            score = sum(1 for kw in keywords_lower if kw in text)
            if score > 0:
                article.relevance_score = score / len(keywords_lower)
                filtered.append(article)

        return filtered

    @staticmethod
    def get_available_feeds() -> Dict[str, Any]:
        """Return the available RSS feed catalog for UI display"""
        catalog = {}
        for region, categories in RSS_FEEDS.items():
            catalog[region] = {}
            for category, feeds in categories.items():
                catalog[region][category] = [f["name"] for f in feeds]
        return catalog
