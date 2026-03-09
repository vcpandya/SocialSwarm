"""
Scenario Templates for Domain-Specific Simulations
Pre-configured simulation setups for regulatory, financial, and election scenarios.
Each template provides default agent archetypes, event configurations, and analysis prompts.
"""

from typing import Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class ScenarioTemplate:
    """A pre-configured simulation scenario"""
    id: str
    name: str
    description: str
    category: str  # "regulatory", "financial", "election", "general"

    # Default agent archetypes for this scenario
    agent_archetypes: List[Dict[str, Any]] = field(default_factory=list)

    # Default initial events/posts
    default_events: List[Dict[str, Any]] = field(default_factory=list)

    # Suggested simulation parameters
    suggested_config: Dict[str, Any] = field(default_factory=dict)

    # Analysis prompts specific to this scenario
    analysis_prompts: List[str] = field(default_factory=list)

    # Relevant news categories for auto-feeding
    news_categories: List[str] = field(default_factory=list)

    # Recommended platforms
    recommended_platforms: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "agent_archetypes": self.agent_archetypes,
            "default_events": self.default_events,
            "suggested_config": self.suggested_config,
            "analysis_prompts": self.analysis_prompts,
            "news_categories": self.news_categories,
            "recommended_platforms": self.recommended_platforms
        }


# ============================================================
# SCENARIO TEMPLATES
# ============================================================

SCENARIO_TEMPLATES = {

    # --- REGULATORY & COMPLIANCE ---

    "regulatory_policy_impact": ScenarioTemplate(
        id="regulatory_policy_impact",
        name="Regulatory Policy Impact Analysis",
        description="Simulate public discourse around a new regulation or policy change. "
                    "Analyze how different stakeholders react, spread information, and form opinions.",
        category="regulatory",
        agent_archetypes=[
            {"type": "regulator", "count": 2, "stance": "supportive", "influence": 3.0,
             "description": "Government official or regulatory body spokesperson"},
            {"type": "industry_representative", "count": 5, "stance": "opposing", "influence": 2.0,
             "description": "Business leader or industry association representative"},
            {"type": "consumer_advocate", "count": 3, "stance": "supportive", "influence": 1.5,
             "description": "Consumer rights activist or NGO representative"},
            {"type": "legal_expert", "count": 2, "stance": "neutral", "influence": 2.0,
             "description": "Legal analyst or compliance expert"},
            {"type": "journalist", "count": 3, "stance": "observer", "influence": 2.5,
             "description": "Media reporter covering regulatory affairs"},
            {"type": "general_public", "count": 15, "stance": "neutral", "influence": 0.8,
             "description": "General public with varying levels of awareness"},
        ],
        suggested_config={
            "total_simulation_hours": 96,
            "timezone": "asia_kolkata",
            "echo_chamber_strength": 0.4,
        },
        analysis_prompts=[
            "What are the main arguments for and against this regulation?",
            "How does public sentiment shift over time after the announcement?",
            "Which stakeholder groups have the most influence on public opinion?",
            "What misinformation or misconceptions are spreading?",
        ],
        news_categories=["general", "business"],
        recommended_platforms=["twitter", "reddit"],
    ),

    "data_privacy_regulation": ScenarioTemplate(
        id="data_privacy_regulation",
        name="Data Privacy Regulation Response",
        description="Simulate reactions to data privacy legislation (like India's DPDP Act or GDPR-style rules). "
                    "Track how tech companies, users, and advocates respond.",
        category="regulatory",
        agent_archetypes=[
            {"type": "tech_company", "count": 4, "stance": "opposing", "influence": 2.5,
             "description": "Technology company representative concerned about compliance costs"},
            {"type": "privacy_advocate", "count": 3, "stance": "supportive", "influence": 2.0,
             "description": "Digital rights activist or privacy researcher"},
            {"type": "government_official", "count": 2, "stance": "supportive", "influence": 3.0,
             "description": "Government ministry or data protection authority"},
            {"type": "startup_founder", "count": 3, "stance": "neutral", "influence": 1.5,
             "description": "Startup ecosystem participant"},
            {"type": "tech_journalist", "count": 2, "stance": "observer", "influence": 2.0,
             "description": "Technology and policy journalist"},
            {"type": "social_media_user", "count": 16, "stance": "neutral", "influence": 0.8,
             "description": "Regular social media user"},
        ],
        suggested_config={
            "total_simulation_hours": 72,
            "timezone": "asia_kolkata",
            "echo_chamber_strength": 0.5,
        },
        analysis_prompts=[
            "How do tech companies frame their response to privacy regulations?",
            "What concerns do regular users express about data privacy?",
            "Is there a divide between industry and public opinion?",
        ],
        news_categories=["tech", "general"],
        recommended_platforms=["twitter", "reddit"],
    ),

    # --- FINANCIAL MARKET ---

    "stock_market_event": ScenarioTemplate(
        id="stock_market_event",
        name="Stock Market Event Sentiment",
        description="Simulate social media discourse around a major market event "
                    "(earnings report, IPO, market crash, policy announcement affecting markets).",
        category="financial",
        agent_archetypes=[
            {"type": "retail_investor", "count": 10, "stance": "neutral", "influence": 0.8,
             "description": "Individual retail investor active on social media"},
            {"type": "financial_analyst", "count": 3, "stance": "neutral", "influence": 2.5,
             "description": "Professional market analyst or fund manager"},
            {"type": "financial_journalist", "count": 2, "stance": "observer", "influence": 2.0,
             "description": "Business/financial news reporter"},
            {"type": "company_insider", "count": 1, "stance": "supportive", "influence": 3.0,
             "description": "Company spokesperson or PR representative"},
            {"type": "finfluencer", "count": 3, "stance": "neutral", "influence": 2.0,
             "description": "Financial influencer or YouTube/Twitter personality"},
            {"type": "skeptic", "count": 3, "stance": "opposing", "influence": 1.5,
             "description": "Market skeptic or contrarian investor"},
            {"type": "regulatory_body", "count": 1, "stance": "neutral", "influence": 3.0,
             "description": "SEBI/SEC or market regulator"},
            {"type": "general_public", "count": 7, "stance": "neutral", "influence": 0.5,
             "description": "Non-investor general public observing market news"},
        ],
        suggested_config={
            "total_simulation_hours": 48,
            "timezone": "asia_kolkata",
            "echo_chamber_strength": 0.6,
        },
        analysis_prompts=[
            "What is the overall market sentiment (bullish/bearish)?",
            "How quickly does sentiment shift after the event?",
            "What role do financial influencers play in shaping retail investor sentiment?",
            "Are there signs of FOMO or panic selling in the discourse?",
        ],
        news_categories=["business"],
        recommended_platforms=["twitter", "reddit", "youtube"],
    ),

    "crypto_market_analysis": ScenarioTemplate(
        id="crypto_market_analysis",
        name="Cryptocurrency Market Sentiment",
        description="Simulate crypto community discourse around a major event "
                    "(regulatory crackdown, new token launch, exchange collapse, price movement).",
        category="financial",
        agent_archetypes=[
            {"type": "crypto_maximalist", "count": 5, "stance": "supportive", "influence": 1.5,
             "description": "Dedicated cryptocurrency believer and promoter"},
            {"type": "crypto_skeptic", "count": 3, "stance": "opposing", "influence": 1.5,
             "description": "Cryptocurrency critic or traditional finance advocate"},
            {"type": "trader", "count": 5, "stance": "neutral", "influence": 1.0,
             "description": "Active crypto trader focused on profit"},
            {"type": "developer", "count": 2, "stance": "neutral", "influence": 2.0,
             "description": "Blockchain developer or project contributor"},
            {"type": "influencer", "count": 3, "stance": "supportive", "influence": 2.5,
             "description": "Crypto influencer with large following"},
            {"type": "regulator", "count": 1, "stance": "neutral", "influence": 3.0,
             "description": "Financial regulator or government official"},
            {"type": "newcomer", "count": 6, "stance": "neutral", "influence": 0.5,
             "description": "New to crypto, easily influenced"},
        ],
        suggested_config={
            "total_simulation_hours": 72,
            "timezone": "utc",
            "echo_chamber_strength": 0.7,
        },
        analysis_prompts=[
            "How does community sentiment shift around the event?",
            "What narratives do different groups push?",
            "How susceptible are newcomers to influencer opinions?",
        ],
        news_categories=["tech", "business"],
        recommended_platforms=["twitter", "reddit"],
    ),

    # --- ELECTION & POLITICAL ---

    "election_campaign": ScenarioTemplate(
        id="election_campaign",
        name="Election Campaign Simulation",
        description="Simulate social media discourse during an election campaign. "
                    "Track how different political factions, media, and public interact.",
        category="election",
        agent_archetypes=[
            {"type": "party_a_supporter", "count": 8, "stance": "supportive", "influence": 1.0,
             "description": "Strong supporter of Party/Candidate A"},
            {"type": "party_b_supporter", "count": 8, "stance": "opposing", "influence": 1.0,
             "description": "Strong supporter of Party/Candidate B"},
            {"type": "swing_voter", "count": 6, "stance": "neutral", "influence": 0.8,
             "description": "Undecided voter open to persuasion"},
            {"type": "political_analyst", "count": 2, "stance": "observer", "influence": 2.5,
             "description": "Political commentator or analyst"},
            {"type": "campaign_official", "count": 2, "stance": "supportive", "influence": 2.0,
             "description": "Official campaign spokesperson"},
            {"type": "journalist", "count": 3, "stance": "observer", "influence": 2.5,
             "description": "Political journalist or editor"},
            {"type": "fact_checker", "count": 1, "stance": "neutral", "influence": 2.0,
             "description": "Fact-checking organization representative"},
            {"type": "first_time_voter", "count": 5, "stance": "neutral", "influence": 0.5,
             "description": "Young or first-time voter"},
            {"type": "bot_account", "count": 3, "stance": "supportive", "influence": 0.3,
             "description": "Automated or coordinated inauthentic account"},
        ],
        suggested_config={
            "total_simulation_hours": 168,  # 7 days
            "timezone": "asia_kolkata",
            "echo_chamber_strength": 0.8,
        },
        analysis_prompts=[
            "How polarized is the discourse between political factions?",
            "What narratives are most effective at persuading swing voters?",
            "How does misinformation spread and how effective are fact-checkers?",
            "What is the sentiment trajectory as election day approaches?",
            "Are there echo chambers forming? How impermeable are they?",
        ],
        news_categories=["general"],
        recommended_platforms=["twitter", "whatsapp", "instagram"],
    ),

    "misinformation_spread": ScenarioTemplate(
        id="misinformation_spread",
        name="Misinformation Spread Analysis",
        description="Simulate how misinformation spreads through social media networks "
                    "and analyze the effectiveness of fact-checking and counter-narratives.",
        category="election",
        agent_archetypes=[
            {"type": "misinformation_source", "count": 2, "stance": "supportive", "influence": 1.5,
             "description": "Account that creates or amplifies false information"},
            {"type": "amplifier", "count": 5, "stance": "supportive", "influence": 1.0,
             "description": "Account that shares content without verification"},
            {"type": "fact_checker", "count": 2, "stance": "opposing", "influence": 2.0,
             "description": "Fact-checking organization or journalist"},
            {"type": "media_outlet", "count": 2, "stance": "observer", "influence": 3.0,
             "description": "Mainstream media organization"},
            {"type": "platform_moderator", "count": 1, "stance": "neutral", "influence": 2.5,
             "description": "Platform trust & safety representative"},
            {"type": "general_public", "count": 18, "stance": "neutral", "influence": 0.8,
             "description": "General social media users with varying media literacy"},
        ],
        suggested_config={
            "total_simulation_hours": 48,
            "timezone": "asia_kolkata",
            "echo_chamber_strength": 0.6,
        },
        analysis_prompts=[
            "How quickly does misinformation spread compared to corrections?",
            "What percentage of agents end up believing or sharing false information?",
            "How effective are fact-checkers at countering misinformation?",
            "What characteristics make users more susceptible to misinformation?",
        ],
        news_categories=["general"],
        recommended_platforms=["twitter", "whatsapp"],
    ),
}


def get_template(template_id: str) -> ScenarioTemplate:
    """Get a scenario template by ID"""
    return SCENARIO_TEMPLATES.get(template_id)


def list_templates(category: str = None) -> List[Dict[str, Any]]:
    """List available templates, optionally filtered by category"""
    templates = []
    for t in SCENARIO_TEMPLATES.values():
        if category and t.category != category:
            continue
        templates.append({
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "category": t.category,
            "agent_count": sum(a["count"] for a in t.agent_archetypes),
            "recommended_platforms": t.recommended_platforms,
        })
    return templates
