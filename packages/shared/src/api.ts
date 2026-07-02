// Platform-agnostic API client shared by the web (React) and mobile (React
// Native) apps. Uses only `fetch`, so it runs unchanged on both. Token storage
// is injected so each platform can persist it however it likes (memory on web,
// AsyncStorage/SecureStore on mobile).
import type {
  Listing,
  Offer,
  OfferAction,
  Subscription,
  SubscriptionTier,
  UserPublic,
} from "./types";

export interface TokenStore {
  get(): string | null;
  set(token: string | null): void;
}

/** Default in-memory token store; adequate for web. */
export function memoryTokenStore(): TokenStore {
  let token: string | null = null;
  return { get: () => token, set: (t) => (token = t) };
}

export interface ApiClient {
  login(email: string, password: string): Promise<string>;
  register(payload: {
    email: string;
    password: string;
    display_name: string;
    home_district?: string;
  }): Promise<UserPublic>;
  me(): Promise<UserPublic>;
  listListings(filters?: Record<string, string>): Promise<Listing[]>;
  createListing(payload: Record<string, unknown>): Promise<Listing>;
  makeOffer(
    listingId: number,
    payload: Record<string, unknown>,
  ): Promise<{ accepted_for_review: boolean; message: string; delivery_fee: number | null }>;
  askSpecsGuard(
    listingId: number,
    question: string,
  ): Promise<{ answer: string; specs_guard_enabled: boolean }>;
  myListings(): Promise<Listing[]>;
  offersForListing(listingId: number): Promise<Offer[]>;
  offerAction(offerId: number, action: OfferAction): Promise<Offer>;
  getSubscription(): Promise<Subscription>;
  upgrade(tier: SubscriptionTier): Promise<Subscription>;
}

export function createApiClient(baseUrl: string, tokens: TokenStore = memoryTokenStore()): ApiClient {
  async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(init.headers as Record<string, string>),
    };
    const token = tokens.get();
    if (token) headers.Authorization = `Bearer ${token}`;

    const res = await fetch(`${baseUrl}${path}`, { ...init, headers });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      throw new Error((detail as { detail?: string }).detail ?? `Request failed (${res.status})`);
    }
    return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
  }

  return {
    async login(email, password) {
      // OAuth2 password flow expects a form-encoded body.
      const body = new URLSearchParams({ username: email, password });
      const res = await fetch(`${baseUrl}/auth/login`, { method: "POST", body });
      if (!res.ok) throw new Error("Login failed");
      const data = (await res.json()) as { access_token: string };
      tokens.set(data.access_token);
      return data.access_token;
    },

    register(payload) {
      return request("/auth/register", { method: "POST", body: JSON.stringify(payload) });
    },

    me() {
      return request("/auth/me");
    },

    listListings(filters = {}) {
      const qs = new URLSearchParams(
        Object.entries(filters).filter(([, v]) => v !== ""),
      ).toString();
      return request(`/listings${qs ? `?${qs}` : ""}`);
    },

    createListing(payload) {
      return request("/listings", { method: "POST", body: JSON.stringify(payload) });
    },

    makeOffer(listingId, payload) {
      return request(`/listings/${listingId}/offers`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },

    askSpecsGuard(listingId, question) {
      return request(`/listings/${listingId}/ask`, {
        method: "POST",
        body: JSON.stringify({ question }),
      });
    },

    myListings() {
      return request("/listings/mine");
    },

    offersForListing(listingId) {
      return request(`/listings/${listingId}/offers`);
    },

    offerAction(offerId, action) {
      return request(`/offers/${offerId}/${action}`, { method: "POST" });
    },

    getSubscription() {
      return request("/subscription");
    },

    upgrade(tier) {
      return request("/subscription/upgrade", { method: "POST", body: JSON.stringify({ tier }) });
    },
  };
}
