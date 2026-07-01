# LakasMarket Backend

FastAPI + SQLAlchemy (PostgreSQL) service implementing LakasMarket's
anti-lowball marketplace logic.

## Layout

```
app/
├── config.py            # env-driven settings
├── database.py          # engine, session, declarative Base
├── models/              # SQLAlchemy ORM models
│   ├── enums.py         # District, SaleMode, OfferStatus, AdabEventType, ...
│   ├── user.py          # User + dual Adab reputation
│   ├── listing.py       # Listing (Hard Floor, sale mode) + KnowledgeQuestion
│   ├── offer.py         # Offer (silent auto-rejection)
│   └── subscription.py  # SaaS tiers + limits
├── core/                # Domain engines (pure logic where possible)
│   ├── anti_lowball.py  # Hard Floor + Take Tonight evaluation
│   ├── knowledge_gateway.py  # quiz grading
│   ├── adab.py          # reputation adjustments
│   ├── logistics.py     # distance-fair delivery fees
│   ├── specs_guard.py   # LLM question generation / Q&A
│   └── security.py      # password hashing + JWT
├── schemas/             # Pydantic request/response models
├── api/                 # routers + dependencies
└── main.py              # app factory
```

## Running

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # set DATABASE_URL / SECRET_KEY / OPENAI_API_KEY
uvicorn app.main:app --reload
```

In `development`, tables are auto-created on startup. For production, generate
Alembic migrations against `Base.metadata` instead.

## Key endpoints

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| POST | `/auth/register` | – | Create account (starts on Basic tier) |
| POST | `/auth/login` | – | OAuth2 password → JWT |
| GET | `/auth/me` | ✅ | Current user + Adab score |
| POST | `/listings` | ✅ | Secure listing creation (tier-limited) |
| GET | `/listings` | – | Browse active listings |
| GET | `/listings/{id}` | – | Listing detail (quiz prompts, no answers) |
| POST | `/listings/{id}/offers` | ✅ | Make an offer — runs Adab gate, Knowledge Gateway, logistics, and Anti-Lowball engine |
| GET | `/listings/{id}/offers` | ✅ (seller) | Seller's offers (auto-rejected lowballs hidden) |

## Tests

```bash
pytest
```

Covers the Anti-Lowball floor/speed logic, logistics fees, and Adab scoring.
