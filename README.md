# LakasMarket

A specialized secondary-market SaaS platform for Brunei, designed to eliminate
"cheap mentality" and aggressive lowballing through automated systems.

LakasMarket protects sellers from insulting offers, redundant questions, and
ghosting by combining a **Hard Floor price engine**, a **Product Knowledge
Gateway**, an **Adab (courtesy) reputation system**, and **distance-fair
logistics** — all wrapped in an AI-assisted "Specs Guard".

## Why LakasMarket exists

Sellers on generic Brunei marketplaces face systemic friction:

| Problem | LakasMarket's answer |
| --- | --- |
| **Lowballing** ("$25 for a $60 item") | **Anti-Lowball Engine** — offers below the seller's Hard Floor are silently rejected so the seller never sees them. |
| **Reading deficit** (asking "is it wired?" on a wired keyboard) | **Product Knowledge Gateway** — buyers must pass a 1–2 question fact-check before chatting. |
| **Speed scalping** ("I'll take it tonight, give me half off") | **Take Tonight premium** — speed discounts are capped at 5–10%. |
| **Ghosting & rudeness** ("Hilang kana tiup angin") | **Adab Score** — reliability + communication points that gate who can message a seller. |
| **Logistical entitlement** (free delivery to Seria/KB) | **Logistics Engine** — automatic distance-fair delivery fees between districts. |

## Tech Stack

- **Frontend:** React (web dashboard) via Vite, structured as a monorepo so
  business logic can be shared with a future React Native app.
- **Backend:** Python + FastAPI for high-performance, async request handling.
- **Database:** PostgreSQL via SQLAlchemy for complex reputation scoring and
  transaction history.
- **AI:** Pluggable LLM provider (OpenAI-compatible) powering the Specs Guard.

## Repository layout

```
LakasMarket/
├── backend/            # FastAPI + SQLAlchemy service
│   └── app/
│       ├── models/     # SQLAlchemy models (User, Listing, Offer, Subscription)
│       ├── schemas/    # Pydantic request/response schemas
│       ├── core/       # Domain engines (anti-lowball, adab, logistics, specs guard)
│       └── api/        # Routers and dependencies
├── frontend/           # React (Vite) web dashboard
└── packages/
    └── shared/         # Cross-platform TS logic reused by web + React Native
```

## Getting started

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then edit DATABASE_URL / SECRET_KEY / OPENAI_API_KEY
uvicorn app.main:app --reload
```

API docs are then available at http://localhost:8000/docs.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Subscription tiers

| Feature | Basic (Free) | Pro | Business |
| --- | --- | --- | --- |
| Active listings | 5 | Unlimited | Unlimited + bulk upload |
| Lowball filter | Standard (20% cap) | Custom + AI negotiation | Fully automated |
| Specs Guard (AI Q&A) | ❌ | ✅ | ✅ Priority |
| Analytics | ❌ | Market demand | Advanced reporting |
| Escrow | ❌ | Optional | Integrated payments |

Recommended Pro pricing: **$7–12 BND / month**.

## Status

This is the initial scaffold: database models, domain engines, and secure
listing/offer endpoints are in place. See `backend/app` for details.
