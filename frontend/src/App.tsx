import { useState } from "react";
import { api } from "./api/client";
import { Dashboard } from "./pages/Dashboard";

export function App() {
  const [loggedIn, setLoggedIn] = useState(false);
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
      </header>
      {loggedIn ? (
        <Dashboard />
      ) : (
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
      )}
    </>
  );
}
