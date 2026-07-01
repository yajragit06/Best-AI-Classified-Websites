import { useState } from "react";
import { api } from "./api/client";
import { Dashboard } from "./pages/Dashboard";
import { SellerDashboard } from "./pages/SellerDashboard";
import { PlanPanel } from "./pages/PlanPanel";

type Tab = "browse" | "mine" | "plan";

export function App() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [tab, setTab] = useState<Tab>("browse");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function login(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.login(email, password);
      setLoggedIn(true);
    } catch {
      setError("Login failed. Register first via the API if you have no account.");
    }
  }

  return (
    <>
      <header className="app">
        <h1>LakasMarket</h1>
        <small>Brunei's anti-lowball marketplace</small>
        {loggedIn && (
          <nav style={{ marginTop: 8, display: "flex", gap: 8 }}>
            <TabButton active={tab === "browse"} onClick={() => setTab("browse")}>
              Browse
            </TabButton>
            <TabButton active={tab === "mine"} onClick={() => setTab("mine")}>
              My Listings
            </TabButton>
            <TabButton active={tab === "plan"} onClick={() => setTab("plan")}>
              Plan
            </TabButton>
          </nav>
        )}
      </header>

      {!loggedIn ? (
        <div className="container">
          <form className="card" onSubmit={login}>
            <h3>Sign in</h3>
            <label>Email</label>
            <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
            <label>Password</label>
            <input
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              type="password"
              required
            />
            {error && <div className="warn">{error}</div>}
            <button>Sign in</button>
          </form>
        </div>
      ) : tab === "browse" ? (
        <Dashboard />
      ) : tab === "mine" ? (
        <SellerDashboard />
      ) : (
        <PlanPanel />
      )}
    </>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      style={{
        background: active ? "#fff" : "transparent",
        color: active ? "#0b6b4f" : "#fff",
        border: "1px solid rgba(255,255,255,0.6)",
        padding: "4px 12px",
      }}
    >
      {children}
    </button>
  );
}
