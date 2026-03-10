"""
Source Scraper for Persona Enrichment
Scrapes web sources (news articles, forums, social media profiles) to extract
real-world context for generating more authentic simulation personas.
Uses only standard library + existing dependencies (no new packages needed).
"""

import json
import re
import html
import socket
import ipaddress
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse

from ..utils.logger import get_logger

logger = get_logger('mirofish.source_scraper')


@dataclass
class ScrapedSource:
    """A scraped web source with extracted content"""
    url: str
    title: str = ""
    content: str = ""  # Main text content
    source_type: str = ""  # "news", "forum", "profile", "social_media", "blog"
    domain: str = ""
    scraped_at: Optional[datetime] = None

    # Extracted entities and context
    mentioned_entities: List[str] = field(default_factory=list)
    key_topics: List[str] = field(default_factory=list)
    sentiment_indicators: List[str] = field(default_factory=list)
    quotes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "content": self.content[:2000],
            "source_type": self.source_type,
            "domain": self.domain,
            "scraped_at": self.scraped_at.isoformat() if self.scraped_at else None,
            "mentioned_entities": self.mentioned_entities,
            "key_topics": self.key_topics,
            "sentiment_indicators": self.sentiment_indicators,
            "quotes": self.quotes[:10],
        }

    def to_entity_context(self) -> str:
        """Convert to text suitable for entity context injection"""
        parts = [f"Source: {self.title} ({self.domain})"]
        if self.content:
            parts.append(f"Content summary: {self.content[:500]}")
        if self.key_topics:
            parts.append(f"Key topics: {', '.join(self.key_topics)}")
        if self.quotes:
            parts.append(f"Notable quotes: {'; '.join(self.quotes[:3])}")
        return "\n".join(parts)


@dataclass
class ScrapeConfig:
    """Configuration for a scraping job"""
    urls: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)  # For filtering relevant content
    max_content_length: int = 5000  # Max chars per source
    extract_quotes: bool = True
    extract_entities: bool = True


class SourceScraper:
    """Scrapes web sources for persona enrichment context"""

    USER_AGENT = "SocialSwarm/1.0 (Academic Research Tool)"
    TIMEOUT = 15

    def _validate_url(self, url: str) -> bool:
        """Validate that a URL does not point to a private/internal IP address (SSRF protection).

        Returns True if the URL is safe to request, False otherwise.
        """
        try:
            parsed = urlparse(url)

            # Only allow http and https schemes
            if parsed.scheme not in ('http', 'https'):
                logger.warning(f"SSRF protection: blocked URL with disallowed scheme '{parsed.scheme}': {url}")
                return False

            hostname = parsed.hostname
            if not hostname:
                logger.warning(f"SSRF protection: blocked URL with no hostname: {url}")
                return False

            # Resolve hostname to IP addresses
            try:
                addr_infos = socket.getaddrinfo(hostname, None)
            except socket.gaierror:
                logger.warning(f"SSRF protection: failed to resolve hostname '{hostname}': {url}")
                return False

            for addr_info in addr_infos:
                ip_str = addr_info[4][0]
                ip = ipaddress.ip_address(ip_str)

                # Check for private/reserved IPv4 ranges
                if ip.is_private:
                    # Covers 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.0/8,
                    # and IPv6 fc00::/7, ::1, fe80::/10, etc.
                    logger.warning(f"SSRF protection: blocked private/internal IP {ip} for URL: {url}")
                    return False

                if ip.is_loopback:
                    logger.warning(f"SSRF protection: blocked loopback IP {ip} for URL: {url}")
                    return False

                if ip.is_link_local:
                    # Covers 169.254.0.0/16 and fe80::/10
                    logger.warning(f"SSRF protection: blocked link-local IP {ip} for URL: {url}")
                    return False

                if ip.is_reserved:
                    logger.warning(f"SSRF protection: blocked reserved IP {ip} for URL: {url}")
                    return False

                # Explicit check for cloud metadata endpoint
                if ip_str == '169.254.169.254':
                    logger.warning(f"SSRF protection: blocked cloud metadata endpoint {ip} for URL: {url}")
                    return False

            return True

        except Exception as e:
            logger.warning(f"SSRF protection: error validating URL '{url}': {e}")
            return False

    def scrape_urls(self, config: ScrapeConfig) -> List[ScrapedSource]:
        """Scrape multiple URLs and extract relevant content"""
        sources = []
        for url in config.urls:
            try:
                if not self._validate_url(url):
                    logger.warning(f"Skipping URL that failed SSRF validation: {url}")
                    continue
                source = self._scrape_single(url, config)
                if source and source.content:
                    sources.append(source)
                    logger.info(f"Scraped: {url} ({len(source.content)} chars)")
            except Exception as e:
                logger.warning(f"Failed to scrape {url}: {e}")
        return sources

    def scrape_to_persona_context(self, sources: List[ScrapedSource]) -> Dict[str, Any]:
        """Convert scraped sources into persona generation context"""
        context = {
            "source_summaries": [],
            "all_topics": [],
            "all_quotes": [],
            "entity_mentions": [],
            "sentiment_cues": [],
        }

        for source in sources:
            context["source_summaries"].append({
                "title": source.title,
                "domain": source.domain,
                "summary": source.content[:300],
                "type": source.source_type,
            })
            context["all_topics"].extend(source.key_topics)
            context["all_quotes"].extend(source.quotes[:5])
            context["entity_mentions"].extend(source.mentioned_entities)
            context["sentiment_cues"].extend(source.sentiment_indicators)

        # Deduplicate
        context["all_topics"] = list(set(context["all_topics"]))[:20]
        context["entity_mentions"] = list(set(context["entity_mentions"]))[:30]
        context["sentiment_cues"] = list(set(context["sentiment_cues"]))[:10]

        return context

    def format_for_prompt(self, sources: List[ScrapedSource]) -> str:
        """Format scraped data as LLM prompt context"""
        if not sources:
            return ""

        text = "\n\n### Real-World Source Context (use to ground personas in reality):\n"
        for i, source in enumerate(sources[:5], 1):
            text += f"\n**Source {i}**: {source.title} ({source.domain})\n"
            text += f"Content: {source.content[:400]}\n"
            if source.quotes:
                text += f"Key quotes: {'; '.join(source.quotes[:2])}\n"
            if source.key_topics:
                text += f"Topics: {', '.join(source.key_topics)}\n"

        return text

    def _scrape_single(self, url: str, config: ScrapeConfig) -> Optional[ScrapedSource]:
        """Scrape a single URL"""
        # Defense-in-depth: validate URL even if caller already checked
        if not self._validate_url(url):
            return None

        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')

        req = Request(url, headers={
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })

        try:
            with urlopen(req, timeout=self.TIMEOUT) as response:
                content_type = response.headers.get('Content-Type', '')
                if 'text/html' not in content_type and 'application/xhtml' not in content_type:
                    logger.warning(f"Skipping non-HTML content: {content_type}")
                    return None

                raw_html = response.read().decode('utf-8', errors='replace')
        except (URLError, HTTPError) as e:
            logger.warning(f"HTTP error for {url}: {e}")
            return None

        # Extract content
        title = self._extract_title(raw_html)
        text_content = self._extract_text(raw_html)
        source_type = self._detect_source_type(domain, raw_html)

        # Truncate content
        text_content = text_content[:config.max_content_length]

        source = ScrapedSource(
            url=url,
            title=title,
            content=text_content,
            source_type=source_type,
            domain=domain,
            scraped_at=datetime.now(),
        )

        # Extract additional features
        if config.extract_quotes:
            source.quotes = self._extract_quotes(raw_html)
        if config.extract_entities:
            source.mentioned_entities = self._extract_entity_names(text_content)
        source.key_topics = self._extract_topics(text_content, config.keywords)
        source.sentiment_indicators = self._extract_sentiment_cues(text_content)

        return source

    def _extract_title(self, html_content: str) -> str:
        """Extract page title"""
        match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
        if match:
            title = html.unescape(match.group(1).strip())
            return re.sub(r'\s+', ' ', title)[:200]

        # Try og:title
        match = re.search(r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\'](.*?)["\']', html_content, re.IGNORECASE)
        if match:
            return html.unescape(match.group(1).strip())[:200]

        return "Untitled"

    def _extract_text(self, html_content: str) -> str:
        """Extract main text content from HTML"""
        # Remove script, style, nav, header, footer tags
        text = re.sub(r'<(script|style|nav|header|footer|aside|noscript)[^>]*>[\s\S]*?</\1>', '', html_content, flags=re.IGNORECASE)

        # Remove all HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)

        # Decode HTML entities
        text = html.unescape(text)

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Remove very short lines (likely navigation remnants)
        lines = text.split('. ')
        meaningful_lines = [l.strip() for l in lines if len(l.strip()) > 30]

        return '. '.join(meaningful_lines)

    def _detect_source_type(self, domain: str, html_content: str) -> str:
        """Detect the type of source"""
        news_domains = ['reuters', 'bbc', 'ndtv', 'thehindu', 'nytimes', 'washingtonpost',
                       'economictimes', 'livemint', 'cnbc', 'aljazeera', 'guardian']
        forum_domains = ['reddit', 'quora', 'stackexchange', 'discourse']
        social_domains = ['twitter', 'x.com', 'facebook', 'instagram', 'linkedin']
        blog_domains = ['medium', 'substack', 'wordpress', 'blogger', 'ghost']

        domain_lower = domain.lower()

        for nd in news_domains:
            if nd in domain_lower:
                return "news"
        for fd in forum_domains:
            if fd in domain_lower:
                return "forum"
        for sd in social_domains:
            if sd in domain_lower:
                return "social_media"
        for bd in blog_domains:
            if bd in domain_lower:
                return "blog"

        return "article"

    def _extract_quotes(self, html_content: str) -> List[str]:
        """Extract quoted text from HTML"""
        quotes = []

        # Blockquote content
        for match in re.finditer(r'<blockquote[^>]*>(.*?)</blockquote>', html_content, re.DOTALL | re.IGNORECASE):
            text = re.sub(r'<[^>]+>', '', match.group(1)).strip()
            if 20 < len(text) < 500:
                quotes.append(html.unescape(text))

        # Quoted text in content
        text = re.sub(r'<[^>]+>', '', html_content)
        text = html.unescape(text)
        for match in re.finditer(r'["\u201c](.*?)["\u201d]', text):
            quote = match.group(1).strip()
            if 20 < len(quote) < 300:
                quotes.append(quote)

        return quotes[:15]

    def _extract_entity_names(self, text: str) -> List[str]:
        """Extract likely entity names (capitalized multi-word phrases)"""
        # Match capitalized sequences (likely proper nouns)
        matches = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', text)
        # Deduplicate and filter common phrases
        common = {'The Government', 'The State', 'New York', 'United States', 'Prime Minister'}
        entities = list(set(m for m in matches if m not in common))
        return entities[:20]

    def _extract_topics(self, text: str, keywords: List[str]) -> List[str]:
        """Extract key topics from text"""
        topics = []
        text_lower = text.lower()

        # Check for keyword matches
        for kw in keywords:
            if kw.lower() in text_lower:
                topics.append(kw)

        # Common topic indicators
        topic_patterns = [
            (r'\b(?:AI|artificial intelligence)\b', 'AI/Technology'),
            (r'\b(?:data privacy|GDPR|data protection)\b', 'Data Privacy'),
            (r'\b(?:election|voting|ballot|candidate)\b', 'Elections'),
            (r'\b(?:stock market|Sensex|Nifty|BSE|NSE)\b', 'Stock Market'),
            (r'\b(?:cryptocurrency|crypto|bitcoin|ethereum)\b', 'Cryptocurrency'),
            (r'\b(?:startup|unicorn|venture capital|VC)\b', 'Startups'),
            (r'\b(?:climate change|global warming|carbon)\b', 'Climate'),
            (r'\b(?:education|university|student|campus)\b', 'Education'),
            (r'\b(?:healthcare|hospital|medical|health)\b', 'Healthcare'),
            (r'\b(?:regulation|compliance|regulatory)\b', 'Regulation'),
        ]

        for pattern, topic in topic_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                topics.append(topic)

        return list(set(topics))[:10]

    def _extract_sentiment_cues(self, text: str) -> List[str]:
        """Extract sentiment-indicating phrases"""
        cues = []
        sentiment_patterns = [
            (r'(?:outrage|furious|angry|protest)', 'negative_strong'),
            (r'(?:concerned|worried|anxious|fear)', 'negative_mild'),
            (r'(?:celebrate|praised|applaud|welcome)', 'positive_strong'),
            (r'(?:hopeful|optimistic|promising)', 'positive_mild'),
            (r'(?:controversial|divisive|polariz)', 'polarizing'),
            (r'(?:misinformation|fake news|misleading)', 'misinformation'),
            (r'(?:viral|trending|breaking)', 'high_engagement'),
        ]

        for pattern, cue in sentiment_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                cues.append(cue)

        return cues
