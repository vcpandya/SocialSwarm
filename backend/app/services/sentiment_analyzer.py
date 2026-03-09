"""
Sentiment & Polarization Analyzer
Analyzes simulation content using LLM to extract sentiment scores and topic stances.
Uses batch processing to efficiently analyze large volumes of posts.
"""

import json
import sqlite3
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime

from openai import OpenAI
from ..config import Config
from ..utils.logger import get_logger
from .proxy_data_loader import ProxyDataLoader

logger = get_logger('mirofish.sentiment')


@dataclass
class SentimentScore:
    """Sentiment analysis result for a single post"""
    post_id: int
    user_id: int
    content_preview: str  # First 100 chars
    sentiment: float  # -1.0 (very negative) to 1.0 (very positive)
    emotions: Dict[str, float]  # e.g. {"anger": 0.3, "joy": 0.1, "fear": 0.5}
    topics: List[str]  # Extracted topics
    stance: Dict[str, str]  # topic -> "support"/"oppose"/"neutral"
    round_num: int = 0


@dataclass
class PolarizationMetrics:
    """Aggregated polarization metrics"""
    overall_sentiment_mean: float
    overall_sentiment_std: float
    sentiment_by_round: List[Dict[str, Any]]  # [{round, mean, std, count}]
    sentiment_by_agent: List[Dict[str, Any]]  # [{agent_id, agent_name, mean, count}]
    topic_sentiment: List[Dict[str, Any]]  # [{topic, mean, std, count}]
    emotion_distribution: Dict[str, float]  # Aggregated emotions
    polarization_index: float  # 0-1, higher = more polarized
    echo_chamber_score: float  # 0-1, higher = stronger echo chambers


class SentimentAnalyzer:
    """Analyzes sentiment and polarization from simulation data"""

    BATCH_SIZE = 10  # Posts per LLM call

    def __init__(self):
        self.client = OpenAI(
            api_key=Config.LLM_API_KEY,
            base_url=Config.LLM_BASE_URL
        )
        self.model = Config.LLM_MODEL_NAME

    def analyze_simulation(self, db_path: str, platform: str = "twitter") -> PolarizationMetrics:
        """Full sentiment analysis of a simulation's posts"""
        posts = self._load_posts(db_path)
        if not posts:
            return self._empty_metrics()

        # Batch analyze posts
        scores = []
        for i in range(0, len(posts), self.BATCH_SIZE):
            batch = posts[i:i + self.BATCH_SIZE]
            batch_scores = self._analyze_batch(batch)
            scores.extend(batch_scores)

        return self._compute_metrics(scores)

    def get_sentiment_timeline(self, db_path: str) -> List[Dict[str, Any]]:
        """Get sentiment over time (by simulated hour)"""
        posts = self._load_posts(db_path)
        if not posts:
            return []

        # Group posts into chronological buckets by created_at
        # Use round-based grouping: split posts into equal-sized time windows
        if len(posts) <= self.BATCH_SIZE:
            # Few posts: analyze all at once, return single data point
            scores = self._analyze_batch(posts)
            if not scores:
                return []
            sentiments = [s.sentiment for s in scores]
            mean_val = sum(sentiments) / len(sentiments)
            return [{
                "round": 0,
                "mean_sentiment": round(mean_val, 3),
                "post_count": len(scores),
                "created_at": posts[0].get("created_at", "")
            }]

        # Split into time-ordered chunks and analyze each
        chunk_size = max(1, len(posts) // 10)  # ~10 time windows
        timeline = []
        round_num = 0

        for i in range(0, len(posts), chunk_size):
            chunk = posts[i:i + chunk_size]
            scores = self._analyze_batch(chunk)
            if scores:
                sentiments = [s.sentiment for s in scores]
                mean_val = sum(sentiments) / len(sentiments)
                timeline.append({
                    "round": round_num,
                    "mean_sentiment": round(mean_val, 3),
                    "post_count": len(scores),
                    "created_at": chunk[0].get("created_at", "")
                })
            round_num += 1

        return timeline

    def _load_posts(self, db_path: str) -> List[Dict]:
        """Load posts from simulation database"""
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, content, created_at, num_likes
                FROM post
                WHERE content IS NOT NULL AND content != ''
                ORDER BY created_at
            """)
            posts = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return posts
        except Exception as e:
            logger.error(f"Failed to load posts from {db_path}: {e}")
            return []

    def _analyze_batch(self, posts: List[Dict]) -> List[SentimentScore]:
        """Analyze a batch of posts using LLM"""
        posts_text = ""
        for i, post in enumerate(posts):
            content = post.get("content", "")[:500]  # Truncate long posts
            posts_text += f"\n[Post {i+1}] (id={post['id']}, user={post['user_id']}): {content}\n"

        # Add few-shot calibration examples from proxy data
        loader = ProxyDataLoader.get_instance()
        calibration_text = loader.format_sentiment_examples_for_prompt(limit=4)

        prompt = f"""Analyze the sentiment of each post below. For each post return:
- sentiment: float from -1.0 (very negative) to 1.0 (very positive)
- emotions: object with scores 0-1 for: anger, joy, sadness, fear, surprise, disgust
- topics: array of 1-3 main topics discussed
- stance: object mapping each topic to "support", "oppose", or "neutral"
{calibration_text}
Posts to analyze:
{posts_text}

Return a JSON array with one object per post, in order. Each object must have: post_id, sentiment, emotions, topics, stance.
Return ONLY valid JSON, no markdown."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a sentiment analysis expert. Return pure JSON arrays only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )

            result_text = response.choices[0].message.content.strip()
            # Clean potential markdown fencing
            if result_text.startswith("```"):
                result_text = result_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

            results = json.loads(result_text)

            scores = []
            for i, (result, post) in enumerate(zip(results, posts)):
                scores.append(SentimentScore(
                    post_id=post["id"],
                    user_id=post["user_id"],
                    content_preview=post.get("content", "")[:100],
                    sentiment=float(result.get("sentiment", 0)),
                    emotions=result.get("emotions", {}),
                    topics=result.get("topics", []),
                    stance=result.get("stance", {}),
                ))
            return scores

        except Exception as e:
            logger.warning(f"Batch sentiment analysis failed: {e}")
            # Return neutral scores as fallback
            return [
                SentimentScore(
                    post_id=p["id"], user_id=p["user_id"],
                    content_preview=p.get("content", "")[:100],
                    sentiment=0.0, emotions={}, topics=[], stance={}
                ) for p in posts
            ]

    def _compute_metrics(self, scores: List[SentimentScore]) -> PolarizationMetrics:
        """Compute aggregated metrics from individual scores"""
        if not scores:
            return self._empty_metrics()

        sentiments = [s.sentiment for s in scores]
        mean_sent = sum(sentiments) / len(sentiments)
        std_sent = (sum((s - mean_sent) ** 2 for s in sentiments) / len(sentiments)) ** 0.5

        # Sentiment by agent
        agent_scores = {}
        for s in scores:
            if s.user_id not in agent_scores:
                agent_scores[s.user_id] = []
            agent_scores[s.user_id].append(s.sentiment)

        sentiment_by_agent = [
            {"agent_id": uid, "mean": round(sum(vals)/len(vals), 3), "count": len(vals)}
            for uid, vals in agent_scores.items()
        ]

        # Topic sentiment
        topic_scores = {}
        for s in scores:
            for topic in s.topics:
                if topic not in topic_scores:
                    topic_scores[topic] = []
                topic_scores[topic].append(s.sentiment)

        topic_sentiment = [
            {
                "topic": t,
                "mean": round(sum(vals)/len(vals), 3),
                "std": round((sum((v - sum(vals)/len(vals))**2 for v in vals)/len(vals))**0.5, 3),
                "count": len(vals)
            }
            for t, vals in topic_scores.items()
        ]
        topic_sentiment.sort(key=lambda x: x["count"], reverse=True)

        # Emotion aggregation
        emotion_totals = {}
        for s in scores:
            for emotion, value in s.emotions.items():
                emotion_totals[emotion] = emotion_totals.get(emotion, 0) + value
        n = len(scores)
        emotion_distribution = {k: round(v/n, 3) for k, v in emotion_totals.items()}

        # Polarization index: bimodality of sentiment distribution
        # Higher when opinions cluster at extremes
        extreme_count = sum(1 for s in sentiments if abs(s) > 0.5)
        polarization_index = min(1.0, extreme_count / max(len(sentiments), 1) * 2)

        # Echo chamber score: how much agents' sentiments cluster
        if len(sentiment_by_agent) > 1:
            agent_means = [a["mean"] for a in sentiment_by_agent]
            agent_std = (sum((m - mean_sent)**2 for m in agent_means) / len(agent_means)) ** 0.5
            echo_chamber_score = min(1.0, agent_std * 2)
        else:
            echo_chamber_score = 0.0

        return PolarizationMetrics(
            overall_sentiment_mean=round(mean_sent, 3),
            overall_sentiment_std=round(std_sent, 3),
            sentiment_by_round=[],  # Populated if round data available
            sentiment_by_agent=sentiment_by_agent[:50],  # Top 50
            topic_sentiment=topic_sentiment[:20],  # Top 20 topics
            emotion_distribution=emotion_distribution,
            polarization_index=round(polarization_index, 3),
            echo_chamber_score=round(echo_chamber_score, 3)
        )

    def _empty_metrics(self) -> PolarizationMetrics:
        return PolarizationMetrics(
            overall_sentiment_mean=0, overall_sentiment_std=0,
            sentiment_by_round=[], sentiment_by_agent=[],
            topic_sentiment=[], emotion_distribution={},
            polarization_index=0, echo_chamber_score=0
        )
