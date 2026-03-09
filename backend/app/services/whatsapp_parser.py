"""
WhatsApp chat export parser for ingesting real WhatsApp data into
SocialSwarm's knowledge graph system.

Handles the standard .txt export format produced by WhatsApp's
"Export Chat" feature, supporting both 12h and 24h timestamp formats,
system messages, multi-line messages, and media markers.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict


# --------------------------------------------------------------------------- #
# Data classes
# --------------------------------------------------------------------------- #

@dataclass
class WhatsAppMessage:
    timestamp: datetime
    sender: str
    content: str
    is_system_message: bool = False
    is_media: bool = False


@dataclass
class WhatsAppChat:
    group_name: Optional[str]
    messages: List[WhatsAppMessage]
    participants: List[str]
    start_date: Optional[datetime]
    end_date: Optional[datetime]


# --------------------------------------------------------------------------- #
# Regex patterns
# --------------------------------------------------------------------------- #

# Matches the timestamp + separator that begins every new WhatsApp line.
# Captures: date_str, time_str, am_pm (optional), rest_of_line
#
# Examples matched:
#   12/25/22, 10:30 AM -        (US short)
#   25/12/2022, 10:30 -         (24h with 4-digit year)
#   1/1/23, 12:00 AM -          (single-digit month/day)
_LINE_RE = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4}),\s+"   # date
    r"(\d{1,2}:\d{2})"                    # time  HH:MM
    r"(?:\s*(AM|PM|am|pm))?"              # optional AM/PM
    r"\s+-\s+"                             # separator  " - "
    r"(.+)$",                              # rest of line
    re.MULTILINE,
)

# After the " - " separator, a user message looks like "Name: text".
# System messages have no colon-separated sender.
_SENDER_RE = re.compile(r"^(.+?):\s(.*)$", re.DOTALL)

# Known system message patterns (substring checks, case-insensitive).
_SYSTEM_PATTERNS = [
    "messages and calls are end-to-end encrypted",
    "created group",
    "added",
    "removed",
    "left",
    "changed the subject",
    "changed this group's icon",
    "changed the group description",
    "you were added",
    "security code changed",
    "disappeared messages",
]

# Group name extraction from system messages.
_GROUP_CREATED_RE = re.compile(
    r'^(.+?)\s+created group\s+"(.+?)"$', re.IGNORECASE
)


# --------------------------------------------------------------------------- #
# Parser
# --------------------------------------------------------------------------- #

class WhatsAppParser:
    """Parse a WhatsApp chat export (.txt) and produce structured data
    suitable for Zep graph ingestion."""

    # ----- public API ------------------------------------------------------ #

    def parse_export(self, content: str) -> WhatsAppChat:
        """Parse raw WhatsApp export text into a *WhatsAppChat* object."""
        # Normalise line endings.
        content = content.replace("\r\n", "\n").replace("\r", "\n")

        raw_blocks = self._split_into_blocks(content)
        messages: List[WhatsAppMessage] = []
        group_name: Optional[str] = None
        participants_set: set = set()

        for ts_str, ampm, body in raw_blocks:
            timestamp = self._parse_timestamp(ts_str, ampm)

            # Try to detect group name from "X created group "Y"" messages.
            m_group = _GROUP_CREATED_RE.match(body)
            if m_group and group_name is None:
                group_name = m_group.group(2)

            # Determine sender vs system message.
            m_sender = _SENDER_RE.match(body)
            if m_sender:
                sender = m_sender.group(1).strip()
                text = m_sender.group(2).strip()
                is_system = False
                is_media = text == "<Media omitted>"
                participants_set.add(sender)
            else:
                # System message (no colon-separated sender).
                sender = ""
                text = body.strip()
                is_system = True
                is_media = False

            # Double-check: some system messages contain a colon in the
            # sender field but are still system events.
            if not is_system and self._is_system_content(body):
                is_system = True

            messages.append(WhatsAppMessage(
                timestamp=timestamp,
                sender=sender,
                content=text,
                is_system_message=is_system,
                is_media=is_media,
            ))

        start_date = messages[0].timestamp if messages else None
        end_date = messages[-1].timestamp if messages else None

        return WhatsAppChat(
            group_name=group_name,
            messages=messages,
            participants=sorted(participants_set),
            start_date=start_date,
            end_date=end_date,
        )

    def to_graph_documents(self, chat: WhatsAppChat) -> List[Dict]:
        """Convert a parsed chat into a list of text chunks ready for Zep.

        Each dict has the shape ``{"data": str, "type": "text"}`` so it can
        be passed directly to ``EpisodeData(data=..., type=...)`` in the
        graph builder pipeline.

        Messages are grouped into chronological windows (up to
        *window_size* messages) to keep each chunk a manageable length while
        preserving conversational context.
        """
        window_size = 20
        user_messages = [
            m for m in chat.messages
            if not m.is_system_message and not m.is_media
        ]
        if not user_messages:
            return []

        documents: List[Dict] = []
        for i in range(0, len(user_messages), window_size):
            window = user_messages[i:i + window_size]
            lines: List[str] = []
            if chat.group_name:
                lines.append(f"[WhatsApp group: {chat.group_name}]")
            for msg in window:
                ts = msg.timestamp.strftime("%Y-%m-%d %H:%M")
                lines.append(f"[{ts}] {msg.sender}: {msg.content}")
            documents.append({
                "data": "\n".join(lines),
                "type": "text",
            })

        return documents

    def get_participants(self, chat: WhatsAppChat) -> List[Dict]:
        """Return unique participants with basic metadata.

        Each entry:
        ``{"name": str, "message_count": int, "first_seen": str, "last_seen": str}``
        """
        stats: Dict[str, Dict] = {}
        for msg in chat.messages:
            if msg.is_system_message or not msg.sender:
                continue
            if msg.sender not in stats:
                stats[msg.sender] = {
                    "name": msg.sender,
                    "message_count": 0,
                    "first_seen": msg.timestamp,
                    "last_seen": msg.timestamp,
                }
            stats[msg.sender]["message_count"] += 1
            if msg.timestamp < stats[msg.sender]["first_seen"]:
                stats[msg.sender]["first_seen"] = msg.timestamp
            if msg.timestamp > stats[msg.sender]["last_seen"]:
                stats[msg.sender]["last_seen"] = msg.timestamp

        result: List[Dict] = []
        for info in sorted(stats.values(), key=lambda x: -x["message_count"]):
            result.append({
                "name": info["name"],
                "message_count": info["message_count"],
                "first_seen": info["first_seen"].isoformat(),
                "last_seen": info["last_seen"].isoformat(),
            })
        return result

    def get_conversation_summary(self, chat: WhatsAppChat) -> str:
        """Generate a concise text summary of the chat suitable for LLM
        processing or as a graph episode preamble."""
        parts: List[str] = []

        if chat.group_name:
            parts.append(f"WhatsApp group chat: \"{chat.group_name}\"")
        else:
            parts.append("WhatsApp chat")

        if chat.participants:
            parts.append(f"Participants ({len(chat.participants)}): {', '.join(chat.participants)}")

        total = len(chat.messages)
        user_msgs = sum(1 for m in chat.messages if not m.is_system_message)
        media_msgs = sum(1 for m in chat.messages if m.is_media)
        parts.append(f"Total messages: {total} ({user_msgs} user, {media_msgs} media)")

        if chat.start_date and chat.end_date:
            fmt = "%Y-%m-%d %H:%M"
            parts.append(f"Period: {chat.start_date.strftime(fmt)} to {chat.end_date.strftime(fmt)}")

        # Top contributors.
        participants = self.get_participants(chat)
        if participants:
            top = participants[:5]
            contrib = "; ".join(
                f"{p['name']} ({p['message_count']})" for p in top
            )
            parts.append(f"Top contributors: {contrib}")

        return "\n".join(parts)

    # ----- internal helpers ------------------------------------------------ #

    @staticmethod
    def _split_into_blocks(content: str) -> List[tuple]:
        """Split the raw text into (timestamp_str, ampm, body) tuples.

        Multi-line messages (continuation lines that don't start with a new
        timestamp) are merged into the preceding message.
        """
        blocks: List[tuple] = []
        for match in _LINE_RE.finditer(content):
            date_part = match.group(1)
            time_part = match.group(2)
            ampm = match.group(3) or ""
            rest = match.group(4)

            ts_str = f"{date_part}, {time_part}"
            blocks.append((ts_str, ampm, rest, match.start(), match.end()))

        # Now handle multi-line: text between end of one match and start of
        # the next that is *not* a new message line belongs to the previous.
        result: List[tuple] = []
        for idx, (ts_str, ampm, rest, _start, end) in enumerate(blocks):
            if idx + 1 < len(blocks):
                next_start = blocks[idx + 1][3]
                continuation = content[end:next_start].strip("\n")
            else:
                continuation = content[end:].strip("\n")

            body = rest
            if continuation:
                body = body + "\n" + continuation
            result.append((ts_str, ampm, body))

        return result

    @staticmethod
    def _parse_timestamp(ts_str: str, ampm: str) -> datetime:
        """Parse a date/time string into a *datetime*.

        Supports:
        - ``M/D/YY`` and ``M/D/YYYY`` (US)
        - ``D/M/YYYY`` (non-US, inferred by 4-digit year with day>12)
        - 12-hour (with AM/PM) and 24-hour formats
        """
        date_part, time_part = ts_str.split(",", 1)
        time_part = time_part.strip()

        parts = date_part.split("/")
        a, b, year_str = int(parts[0]), int(parts[1]), parts[2]
        year = int(year_str)
        if year < 100:
            year += 2000

        # Heuristic: if year_str has 4 digits and a > 12, assume D/M/YYYY.
        if len(year_str) == 4 and a > 12:
            month, day = b, a
        else:
            month, day = a, b

        hour, minute = (int(x) for x in time_part.split(":"))

        if ampm:
            ampm_upper = ampm.upper()
            if ampm_upper == "PM" and hour != 12:
                hour += 12
            elif ampm_upper == "AM" and hour == 12:
                hour = 0

        return datetime(year, month, day, hour, minute)

    @staticmethod
    def _is_system_content(text: str) -> bool:
        """Return True if *text* looks like a system message."""
        lower = text.lower()
        return any(pat in lower for pat in _SYSTEM_PATTERNS)
