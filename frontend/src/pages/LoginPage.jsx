import React, { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import { getToken, login } from "../api";


export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const navigate = useNavigate();

  if (getToken()) {
    return <Navigate to="/" replace />;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setPending(true);
    try {
      await login(email, password);
      navigate("/", { replace: true });
    } catch (err) {
      setError(typeof err.message === "string" ? err.message : "Could not log in");
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-panel">
        <h1>Khabar</h1>
        <p className="tagline">Your news. No noise.</p>
        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            Email
            <input
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>
          {error ? <div className="form-error">{error}</div> : null}
          <button type="submit" disabled={pending}>
            {pending ? "Logging in..." : "Log in"}
          </button>
        </form>
        <p className="auth-switch">
          New to Khabar? <Link to="/signup">Create an account</Link>
        </p>
      </section>
    </main>
  );
}
