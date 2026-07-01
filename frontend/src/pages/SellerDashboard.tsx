import { useEffect, useState } from "react";
import type { Listing } from "@lakasmarket/shared";
import { api, type Offer } from "../api/client";

// Seller's view of their own listings and the offers on them. Auto-rejected
// lowballs never arrive here — the backend hides them to protect sentiment.
export function SellerDashboard() {
  const [listings, setListings] = useState<Listing[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      setListings(await api.myListings());
    } catch (err) {
      setError((err as Error).message);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  return (
    <div className="container">
      <h2>My listings</h2>
      {error && <div className="warn">{error}</div>}
      {listings.length === 0 && <p>You have no listings yet.</p>}
      {listings.map((l) => (
        <SellerListingRow key={l.id} listing={l} />
      ))}
    </div>
  );
}

function SellerListingRow({ listing }: { listing: Listing }) {
  const [offers, setOffers] = useState<Offer[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function loadOffers() {
    setError(null);
    try {
      setOffers(await api.offersForListing(listing.id));
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function act(offerId: number, action: "accept" | "decline" | "complete" | "report-ghost") {
    setBusy(true);
    setError(null);
    try {
      await api.offerAction(offerId, action);
      await loadOffers();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card">
      <h3>{listing.title}</h3>
      <div>
        <span className="badge">{listing.status}</span>
        <span className="badge">B$ {Number(listing.list_price).toFixed(2)}</span>
      </div>
      <div className="floor">
        Floor B$ {listing.hard_floor_price.toFixed(2)} — offers below are auto-declined & hidden.
      </div>

      {offers === null ? (
        <button className="secondary" style={{ marginTop: 8 }} onClick={loadOffers}>
          View offers
        </button>
      ) : offers.length === 0 ? (
        <p>No offers to review. (Lowballs never reach you.)</p>
      ) : (
        <table style={{ width: "100%", marginTop: 8, borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", fontSize: 13 }}>
              <th>Amount</th>
              <th>Speed</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {offers.map((o) => (
              <tr key={o.id} style={{ borderTop: "1px solid #eee", fontSize: 14 }}>
                <td>B$ {Number(o.amount).toFixed(2)}</td>
                <td>{o.is_take_tonight ? "Tonight" : "—"}</td>
                <td>{o.status}</td>
                <td style={{ display: "flex", gap: 6, padding: "6px 0" }}>
                  {o.status === "pending" && (
                    <>
                      <button disabled={busy} onClick={() => act(o.id, "accept")}>
                        Accept
                      </button>
                      <button
                        disabled={busy}
                        className="secondary"
                        onClick={() => act(o.id, "decline")}
                      >
                        Decline
                      </button>
                    </>
                  )}
                  {o.status === "accepted" && (
                    <>
                      <button disabled={busy} onClick={() => act(o.id, "complete")}>
                        Mark sold
                      </button>
                      <button
                        disabled={busy}
                        className="secondary"
                        onClick={() => act(o.id, "report-ghost")}
                      >
                        Report ghosting
                      </button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {error && <div className="warn">{error}</div>}
    </div>
  );
}
