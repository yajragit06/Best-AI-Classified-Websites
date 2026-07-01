// Domain types shared across web (React) and mobile (React Native).

export enum SubscriptionTier {
  Basic = "basic",
  Pro = "pro",
  Business = "business",
}

export enum District {
  Bandar = "bandar",
  BruneiMuara = "brunei_muara",
  Tutong = "tutong",
  Seria = "seria",
  KualaBelait = "kuala_belait",
  Temburong = "temburong",
}

export enum SaleMode {
  Firm = "firm",
  Fast = "fast",
}

export enum ListingStatus {
  Active = "active",
  Reserved = "reserved",
  Sold = "sold",
  Archived = "archived",
}

export interface KnowledgeQuestion {
  id: number;
  prompt: string;
  options: string[];
  ai_generated: boolean;
}

export interface Listing {
  id: number;
  seller_id: number;
  title: string;
  description: string;
  category: string | null;
  list_price: string;
  floor_percent: number;
  hard_floor_price: number;
  sale_mode: SaleMode;
  speed_discount_percent: number;
  district: District;
  delivery_available: boolean;
  min_buyer_adab: number;
  status: ListingStatus;
  created_at: string;
  knowledge_questions: KnowledgeQuestion[];
}

export interface UserPublic {
  id: number;
  display_name: string;
  home_district: District;
  reliability_score: number;
  communication_score: number;
  adab_score: number;
  completed_deals: number;
  created_at: string;
}
