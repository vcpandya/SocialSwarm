<div align="center">

# SocialSwarm

**A Swarm Intelligence Engine for Simulating Social Media Discourse**

*Fork of [MiroFish](https://github.com/666ghj/MiroFish) — enhanced for India & US market research*

[![GitHub Stars](https://img.shields.io/github/stars/vcpandya/SocialSwarm?style=flat-square&color=DAA520)](https://github.com/vcpandya/SocialSwarm/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/vcpandya/SocialSwarm?style=flat-square)](https://github.com/vcpandya/SocialSwarm/network)

</div>

## Overview

SocialSwarm is a multi-agent AI prediction engine that simulates social media discourse to forecast public opinion, policy impact, and market sentiment. Upload seed materials (news articles, reports, or any text), describe your prediction scenario, and SocialSwarm builds a high-fidelity digital world where thousands of AI agents with independent personalities, memories, and behavioral patterns interact freely across simulated social platforms.

**You provide:** Seed materials + a natural language prediction prompt
**SocialSwarm returns:** A detailed prediction report + an interactive digital world you can explore

## Key Features

- **Multi-Platform Simulation** — Twitter and Reddit simulation powered by [OASIS](https://github.com/camel-ai/oasis), with experimental WhatsApp, YouTube, and Instagram support
- **Multi-Timezone Activity Patterns** — Presets for India (IST), US Eastern/Pacific, UK, and China timezones with realistic activity curves
- **Cultural Persona Dimensions** — 11 cultural fields (region, language, urban/rural, caste/community, religion, education medium, income bracket, political leaning, media diet, generation, ethnicity)
- **Hinglish & Multilingual Agents** — Language templates for English, Hinglish, Hindi, Tamil, Telugu, Bengali, Marathi, Spanish, and Mandarin with platform-specific code-switching
- **Sentiment & Polarization Dashboard** — D3.js visualizations: sentiment timeline, topic frequency, emotion radar, agent activity scatter plots
- **What-If Scenario Comparison** — Clone simulations with different parameters and compare outcomes side-by-side
- **Scenario Templates** — Pre-built templates for regulatory impact, financial events, and election campaigns (India/US focused)
- **Research-Backed Archetypes** — 10 persona archetypes grounded in academic research: trolls, bot amplifiers, opinion leaders, echo chamber participants, fact-checkers, and more
- **Real-Time News Feed** — RSS integration with curated India, US, and global news sources for seeding simulations with current events
- **Web Source Scraping** — Scrape news articles, forums, and blogs to enrich persona generation with real-world context
- **Proxy Dataset System** — Few-shot examples for LLM-driven persona generation and sentiment calibration
- **Knowledge Graph (GraphRAG)** — Powered by Zep Cloud for entity extraction, relationship mapping, and memory injection

## Workflow

1. **Graph Building** — Upload seed materials, extract entities and relationships, build a knowledge graph
2. **Environment Setup** — Configure timezone, platforms, language, personas, archetypes, and scenario parameters
3. **Simulation** — Run multi-platform parallel simulation with dynamic temporal memory updates
4. **Report Generation** — ReportAgent analyzes simulation results with a rich toolset (InsightForge, PanoramaSearch, Interviews, QuickSearch)
5. **Deep Interaction** — Chat with any simulated agent or the ReportAgent for follow-up analysis

## Quick Start

### Prerequisites

| Tool | Version | Description |
|------|---------|-------------|
| **Node.js** | 18+ | Frontend runtime (includes npm) |
| **Python** | 3.11 - 3.12 | Backend runtime |
| **uv** | Latest | Python package manager |

### 1. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your API keys
```

**Required variables:**

```env
# LLM API (any OpenAI SDK-compatible provider: OpenAI, Groq, Together, etc.)
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o

# Zep Cloud (free tier available at https://app.getzep.com/)
ZEP_API_KEY=your_zep_api_key
```

### 2. Install Dependencies

```bash
# Install everything (root + frontend + backend)
npm run setup:all
```

Or step by step:

```bash
npm run setup          # Node dependencies (root + frontend)
npm run setup:backend  # Python dependencies (auto-creates venv)
```

### 3. Start Services

```bash
npm run dev  # Starts both frontend and backend
```

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:5001`

Start individually:

```bash
npm run backend   # Backend only
npm run frontend  # Frontend only
```

### Docker Deployment

```bash
cp .env.example .env
docker compose up -d
```

## Project Structure

```
SocialSwarm/
├── frontend/               # Vue 3 + Vite
│   └── src/
│       ├── components/     # Step1-5 workflow + Dashboard
│       ├── views/          # Route views
│       ├── i18n/           # English/Chinese locale files
│       └── api/            # API client functions
├── backend/
│   ├── app/
│   │   ├── api/            # Flask API routes (graph, simulation, report)
│   │   ├── services/       # Core services (profile gen, sentiment, news, scraper)
│   │   └── config.py       # Environment configuration
│   ├── scripts/            # OASIS simulation runner scripts
│   └── data/
│       └── proxy_datasets/ # Few-shot examples for LLM prompting
└── static/                 # Images and assets
```

## Acknowledgments

SocialSwarm is a fork of **[MiroFish](https://github.com/666ghj/MiroFish)**, which received strategic support from Shanda Group. The simulation engine is powered by **[OASIS](https://github.com/camel-ai/oasis)** from the CAMEL-AI team. We thank both teams for their open-source contributions.
