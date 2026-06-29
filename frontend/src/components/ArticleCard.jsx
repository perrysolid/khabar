import React, { useState } from "react";

import { sendFeedback } from "../api";

export default function ArticleCard({
  id,
  title,
  summary,
  url,
  source,
  topic,
  reading_time_minutes
}) {
  const [choice, setChoice] = useState("");
  const [pending, setPending] = useState(false);

  async function vote(feedback) {
    setPending(true);
    try {
      await sendFeedback(id, feedback);
      setChoice(feedback);
    } finally {
      setPending(false);
    }
  }

  const topicClass = `topic-border-${topic || "other"}`;

  return (
    <article className={`article-card ${topicClass}`}>
      <div className="meta-row">
        <span className="topic-name">{topic}</span>
        <span className="source-name">{source}</span>
        <span>🕐 {reading_time_minutes} min</span>
      </div>
      <h2>
        <a href={url} target="_blank" rel="noreferrer">
          {title}
        </a>
      </h2>
      <p className="summary">{summary}</p>
      <div className="feedback-row" aria-label="Article feedback">
        <button
          type="button"
          className={choice === "up" ? "selected" : ""}
          disabled={pending}
          onClick={() => vote("up")}
          aria-label="Thumbs up"
          title="Thumbs up"
        >
          👍
        </button>
        <button
          type="button"
          className={choice === "down" ? "selected" : ""}
          disabled={pending}
          onClick={() => vote("down")}
          aria-label="Thumbs down"
          title="Thumbs down"
        >
          👎
        </button>
      </div>
    </article>
  );
}
