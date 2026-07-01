import { useState } from "react";
import type { Listing } from "@lakasmarket/shared";
import { SaleMode } from "@lakasmarket/shared";
import { OfferForm } from "./OfferForm";

export function ListingCard({ listing }: { listing: Listing }) {
  const [offering, setOffering] = useState(false);

  return (
    <div className="card">
      <h3>{listing.title}</h3>
      <div>
        <span className="badge">{listing.district}</span>
        {listing.sale_mode === SaleMode.Fast && <span className="badge">Take Tonight</span>}
        {listing.knowledge_questions.length > 0 && (
          <span className="badge">Knowledge Gate</span>
        )}
      </div>
      <p>{listing.description}</p>
      <div className="price">B$ {Number(listing.list_price).toFixed(2)}</div>
      <div className="floor">
        Offers below B$ {listing.hard_floor_price.toFixed(2)} are auto-declined.
      </div>
      {listing.min_buyer_adab > 0 && (
        <div className="floor">Requires Adab score ≥ {listing.min_buyer_adab}</div>
      )}

      {offering ? (
        <div style={{ marginTop: 12 }}>
          <OfferForm listing={listing} onClose={() => setOffering(false)} />
        </div>
      ) : (
        <button style={{ marginTop: 12 }} onClick={() => setOffering(true)}>
          Make an offer
        </button>
      )}
    </div>
  );
}
