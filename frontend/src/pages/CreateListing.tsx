import { useState } from "react";
import { District, SaleMode } from "@lakasmarket/shared";
import { api } from "../api/client";

export function CreateListing({ onCreated }: { onCreated: () => void }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [listPrice, setListPrice] = useState("60");
  const [floorPercent, setFloorPercent] = useState("20");
  const [saleMode, setSaleMode] = useState<SaleMode>(SaleMode.Firm);
  const [district, setDistrict] = useState<District>(District.Bandar);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await api.createListing({
        title,
        description,
        list_price: Number(listPrice),
        floor_percent: Number(floorPercent),
        sale_mode: saleMode,
        district,
      });
      onCreated();
      setTitle("");
      setDescription("");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="card" onSubmit={submit}>
      <h3>Create a listing</h3>
      <label>Title</label>
      <input value={title} onChange={(e) => setTitle(e.target.value)} required />
      <label>Description (the Specs Guard reads this)</label>
      <textarea
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        rows={3}
        required
      />
      <div className="grid2">
        <div>
          <label>List price (B$)</label>
          <input
            type="number"
            value={listPrice}
            onChange={(e) => setListPrice(e.target.value)}
            min="1"
          />
        </div>
        <div>
          <label>Max discount / Hard Floor (%)</label>
          <input
            type="number"
            value={floorPercent}
            onChange={(e) => setFloorPercent(e.target.value)}
            min="0"
            max="90"
          />
        </div>
      </div>
      <div className="grid2">
        <div>
          <label>Sale mode</label>
          <select value={saleMode} onChange={(e) => setSaleMode(e.target.value as SaleMode)}>
            <option value={SaleMode.Firm}>Firm — no speed discount</option>
            <option value={SaleMode.Fast}>Fast — capped Take Tonight discount</option>
          </select>
        </div>
        <div>
          <label>District</label>
          <select value={district} onChange={(e) => setDistrict(e.target.value as District)}>
            {Object.values(District).map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>
      </div>
      {error && <div className="warn">{error}</div>}
      <button disabled={busy}>{busy ? "Posting…" : "Post listing"}</button>
    </form>
  );
}
