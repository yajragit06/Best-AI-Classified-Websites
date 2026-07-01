import { useEffect, useState } from "react";
import type { Listing } from "@lakasmarket/shared";
import { api } from "../api/client";
import { ListingCard } from "../components/ListingCard";
import { CreateListing } from "./CreateListing";

export function Dashboard() {
  const [listings, setListings] = useState<Listing[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      setListings(await api.listListings());
    } catch (err) {
      setError((err as Error).message);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  return (
    <div className="container">
      <CreateListing onCreated={refresh} />
      <h2>Active listings</h2>
      {error && <div className="warn">{error}</div>}
      {listings.length === 0 && <p>No listings yet.</p>}
      {listings.map((l) => (
        <ListingCard key={l.id} listing={l} />
      ))}
    </div>
  );
}
