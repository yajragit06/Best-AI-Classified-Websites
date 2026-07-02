// Thin API client. Platform-agnostic (uses fetch), so it can be reused as-is by
// a React Native app.
import type { Listing, SubscriptionTier, UserPublic } from "@lakasmarket/shared";

export interface Offer {
  id: number;
  listing_id: number;
  buyer_id: number;
  amount: string;
  is_take_tonight: boolean;
  status: string;
  delivery_fee: string;
  passed_knowledge_gate: boolean;
  created_at: string;
}

export interface Subscription {
  tier: SubscriptionTier;
  listing_limit: number | null;
  has_specs_guard: boolean;
  started_at: string;
  renews_at: string | null;
}

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

let authToken: string | null = null;

export function setToken(token: string | null): void {
  authToken = token;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string>),
  };
  if (authToken) headers.Authorization = `Bearer ${authToken}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...init, headers });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail ?? `Request failed (${res.status})`);
  }
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}

export const api = {
  async login(email: string, password: string): Promise<string> {
    // OAuth2 password flow expects form-encoded body.
    const body = new URLSearchParams({ username: email, password });
    const res = await fetch(`${BASE_URL}/auth/login`, { method: "POST", body });
    if (!res.ok) throw new Error("Login failed");
    const data = (await res.json()) as { access_token: string };
    setToken(data.access_token);
    return data.access_token;
  },

  register(payload: {
    email: string;
    password: string;
    display_name: string;
    home_district?: string;
  }): Promise<UserPublic> {
    return request("/auth/register", { method: "POST", body: JSON.stringify(payload) });
  },

  me(): Promise<UserPublic> {
    return request("/auth/me");
  },

  listListings(filters: Record<string, string> = {}): Promise<Listing[]> {
    const qs = new URLSearchParams(
      Object.entries(filters).filter(([, v]) => v !== ""),
    ).toString();
    return request(`/listings${qs ? `?${qs}` : ""}`);
  },

  createListing(payload: Record<string, unknown>): Promise<Listing> {
    return request("/listings", { method: "POST", body: JSON.stringify(payload) });
  },

  makeOffer(
    listingId: number,
    payload: Record<string, unknown>,
  ): Promise<{ accepted_for_review: boolean; message: string; delivery_fee: number | null }> {
    return request(`/listings/${listingId}/offers`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  askSpecsGuard(
    listingId: number,
    question: string,
  ): Promise<{ answer: string; specs_guard_enabled: boolean }> {
    return request(`/listings/${listingId}/ask`, {
      method: "POST",
      body: JSON.stringify({ question }),
    });
  },

  myListings(): Promise<Listing[]> {
    return request("/listings/mine");
  },

  offersForListing(listingId: number): Promise<Offer[]> {
    return request(`/listings/${listingId}/offers`);
  },

  offerAction(offerId: number, action: "accept" | "decline" | "complete" | "report-ghost"): Promise<Offer> {
    return request(`/offers/${offerId}/${action}`, { method: "POST" });
  },

  getSubscription(): Promise<Subscription> {
    return request("/subscription");
  },

  upgrade(tier: SubscriptionTier): Promise<Subscription> {
    return request("/subscription/upgrade", {
      method: "POST",
      body: JSON.stringify({ tier }),
    });
  },
};
