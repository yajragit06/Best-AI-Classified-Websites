"""End-to-end API tests covering the auth, listing, and offer flows."""
from tests.conftest import auth_headers

LISTING = {
    "title": "Mechanical keyboard",
    "description": "A wired mechanical keyboard, barely used, no box.",
    "list_price": 100,
    "floor_percent": 20,  # hard floor = 80
}


def test_register_and_me(client):
    headers = auth_headers(client, "seller@example.com")
    me = client.get("/auth/me", headers=headers).json()
    assert me["display_name"] == "seller"
    assert me["adab_score"] == 70.0  # neutral baseline


def test_listing_creation_requires_auth(client):
    assert client.post("/listings", json=LISTING).status_code == 401


def test_create_and_browse_listing(client):
    headers = auth_headers(client, "seller@example.com")
    res = client.post("/listings", json=LISTING, headers=headers)
    assert res.status_code == 201
    body = res.json()
    assert body["hard_floor_price"] == 80.0
    assert body["seller"]["display_name"] == "seller"

    listings = client.get("/listings").json()
    assert len(listings) == 1
    assert listings[0]["title"] == LISTING["title"]


def test_search_filter(client):
    headers = auth_headers(client, "seller@example.com")
    client.post("/listings", json=LISTING, headers=headers)
    client.post(
        "/listings",
        json={**LISTING, "title": "Office chair", "description": "Ergonomic chair"},
        headers=headers,
    )
    assert len(client.get("/listings?q=keyboard").json()) == 1
    assert len(client.get("/listings?max_price=1").json()) == 0


def test_basic_tier_listing_limit(client):
    headers = auth_headers(client, "seller@example.com")
    for i in range(5):
        r = client.post("/listings", json={**LISTING, "title": f"Item {i}"}, headers=headers)
        assert r.status_code == 201
    # 6th exceeds the Basic tier cap of 5.
    r = client.post("/listings", json={**LISTING, "title": "Item 6"}, headers=headers)
    assert r.status_code == 402


def _create_listing(client, headers, **overrides) -> int:
    res = client.post("/listings", json={**LISTING, **overrides}, headers=headers)
    assert res.status_code == 201
    return res.json()["id"]


def test_lowball_is_silently_rejected(client):
    seller = auth_headers(client, "seller@example.com")
    buyer = auth_headers(client, "buyer@example.com")
    lid = _create_listing(client, seller)

    res = client.post(f"/listings/{lid}/offers", json={"amount": 25}, headers=buyer)
    assert res.status_code == 201
    assert res.json()["accepted_for_review"] is False  # neutral to buyer

    # Seller never sees the lowball.
    seller_offers = client.get(f"/listings/{lid}/offers", headers=seller).json()
    assert seller_offers == []


def test_fair_offer_reaches_seller(client):
    seller = auth_headers(client, "seller@example.com")
    buyer = auth_headers(client, "buyer@example.com")
    lid = _create_listing(client, seller)

    res = client.post(f"/listings/{lid}/offers", json={"amount": 85}, headers=buyer)
    assert res.json()["accepted_for_review"] is True

    seller_offers = client.get(f"/listings/{lid}/offers", headers=seller).json()
    assert len(seller_offers) == 1
    assert seller_offers[0]["status"] == "pending"


def test_knowledge_gateway_blocks_wrong_answer(client):
    seller = auth_headers(client, "seller@example.com")
    buyer = auth_headers(client, "buyer@example.com")
    res = client.post(
        "/listings",
        json={
            **LISTING,
            "knowledge_questions": [
                {"prompt": "Wired or wireless?", "options": ["Wired", "Wireless"], "correct_index": 0}
            ],
        },
        headers=seller,
    )
    lid = res.json()["id"]
    qid = res.json()["knowledge_questions"][0]["id"]

    # Wrong answer -> blocked.
    wrong = client.post(
        f"/listings/{lid}/offers",
        json={"amount": 90, "quiz_answers": {str(qid): 1}},
        headers=buyer,
    )
    assert wrong.status_code == 422

    # Correct answer -> passes the gate.
    ok = client.post(
        f"/listings/{lid}/offers",
        json={"amount": 90, "quiz_answers": {str(qid): 0}},
        headers=buyer,
    )
    assert ok.status_code == 201
    assert ok.json()["accepted_for_review"] is True


def test_adab_gate_blocks_low_score_buyer(client):
    seller = auth_headers(client, "seller@example.com")
    buyer = auth_headers(client, "buyer@example.com")
    lid = _create_listing(client, seller, min_buyer_adab=90)  # baseline buyer has 70
    res = client.post(f"/listings/{lid}/offers", json={"amount": 90}, headers=buyer)
    assert res.status_code == 403


def test_accept_and_complete_rewards_adab(client):
    seller = auth_headers(client, "seller@example.com")
    buyer = auth_headers(client, "buyer@example.com")
    lid = _create_listing(client, seller)
    client.post(f"/listings/{lid}/offers", json={"amount": 85}, headers=buyer)

    offer = client.get(f"/listings/{lid}/offers", headers=seller).json()[0]
    assert client.post(f"/offers/{offer['id']}/accept", headers=seller).status_code == 200
    completed = client.post(f"/offers/{offer['id']}/complete", headers=seller)
    assert completed.status_code == 200

    buyer_me = client.get("/auth/me", headers=buyer).json()
    assert buyer_me["completed_deals"] == 1
    assert buyer_me["reliability_score"] > 70.0


def test_report_ghost_penalises_buyer(client):
    seller = auth_headers(client, "seller@example.com")
    buyer = auth_headers(client, "buyer@example.com")
    lid = _create_listing(client, seller)
    client.post(f"/listings/{lid}/offers", json={"amount": 85}, headers=buyer)
    offer = client.get(f"/listings/{lid}/offers", headers=seller).json()[0]
    client.post(f"/offers/{offer['id']}/accept", headers=seller)
    client.post(f"/offers/{offer['id']}/report-ghost", headers=seller)

    buyer_me = client.get("/auth/me", headers=buyer).json()
    assert buyer_me["reliability_score"] < 70.0


def test_subscription_upgrade(client):
    headers = auth_headers(client, "seller@example.com")
    assert client.get("/subscription", headers=headers).json()["tier"] == "basic"
    res = client.post("/subscription/upgrade", json={"tier": "pro"}, headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["tier"] == "pro"
    assert body["listing_limit"] is None
    assert body["has_specs_guard"] is True
