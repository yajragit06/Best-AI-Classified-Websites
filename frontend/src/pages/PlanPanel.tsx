import { useEffect, useState } from "react";
import { SubscriptionTier } from "@lakasmarket/shared";
import { api, type Subscription } from "../api/client";

const TIERS: { tier: SubscriptionTier; name: string; blurb: string; price: string }[] = [
  { tier: SubscriptionTier.Basic, name: "Basic", blurb: "Up to 5 listings, standard 20% floor.", price: "Free" },
  { tier: SubscriptionTier.Pro, name: "Pro", blurb: "Unlimited listings, AI Specs Guard, analytics.", price: "B$7–12 / mo" },
  { tier: SubscriptionTier.Business, name: "Business", blurb: "Bulk tools, integrated escrow, priority support.", price: "Contact us" },
];

export function PlanPanel() {
  const [sub, setSub] = useState<Subscription | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function refresh() {
    try {
      setSub(await api.getSubscription());
    } catch (err) {
      setError((err as Error).message);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function upgrade(tier: SubscriptionTier) {
    setBusy(true);
    setError(null);
    try {
      setSub(await api.upgrade(tier));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="container">
      <h2>Your plan</h2>
      {error && <div className="warn">{error}</div>}
      {sub && (
        <p>
          Current tier: <strong>{sub.tier}</strong>
          {" · "}
          {sub.listing_limit === null ? "Unlimited listings" : `${sub.listing_limit} listings`}
          {sub.has_specs_guard ? " · Specs Guard on" : ""}
        </p>
      )}
      <div className="grid2">
        {TIERS.map((t) => {
          const current = sub?.tier === t.tier;
          return (
            <div className="card" key={t.tier}>
              <h3>{t.name}</h3>
              <div className="price">{t.price}</div>
              <p>{t.blurb}</p>
              <button
                disabled={busy || current}
                className={current ? "secondary" : undefined}
                onClick={() => upgrade(t.tier)}
              >
                {current ? "Current plan" : `Switch to ${t.name}`}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
