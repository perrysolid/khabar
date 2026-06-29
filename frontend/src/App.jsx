import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  BrowserRouter,
  Link,
  Navigate,
  Route,
  Routes,
  useNavigate
} from "react-router-dom";

import { clearToken, getTodayDigest, getToken } from "./api";
import ArticleCard from "./components/ArticleCard";
import DigestHeader from "./components/DigestHeader";
import TopicBreakdown from "./components/TopicBreakdown";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import "./index.css";

function ProtectedRoute({ children }) {
  if (!getToken()) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function DigestPage() {
  const [digest, setDigest] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    getTodayDigest()
      .then(setDigest)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <main className="page">
        <section className="state-panel">Loading today's digest...</section>
      </main>
    );
  }

  if (error) {
    return (
      <main className="page">
        <section className="state-panel error">{error}</section>
      </main>
    );
  }

  const articles = digest?.articles || [];
  const normalizedSearch = searchQuery.trim().toLowerCase();
  const filteredArticles = normalizedSearch
    ? articles.filter((article) =>
        (article.title || "").toLowerCase().includes(normalizedSearch)
      )
    : articles;

  return (
    <main className="page">
      <nav className="top-nav" aria-label="Account">
        <Link to="/" className="brand-link">Khabar</Link>
        <button
          type="button"
          onClick={() => {
            clearToken();
            navigate("/login", { replace: true });
          }}
        >
          Log out
        </button>
      </nav>
      <DigestHeader date={digest.date} count={articles.length} />
      <TopicBreakdown breakdown={digest.topic_breakdown} />
      <label className="search-bar">
        <span>Search headlines</span>
        <input
          type="search"
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.target.value)}
          placeholder="Search loaded stories"
        />
      </label>
      <section className="article-list" aria-label="Daily news articles">
        {articles.length === 0 ? (
          <div className="state-panel">No stories are ready yet.</div>
        ) : filteredArticles.length === 0 ? (
          <div className="state-panel">No headlines match your search.</div>
        ) : (
          filteredArticles.map((article) => <ArticleCard key={article.id} {...article} />)
        )}
      </section>
    </main>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <DigestPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

createRoot(document.getElementById("root")).render(<App />);
