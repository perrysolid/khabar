import React from "react";

export default function TopicBreakdown({ breakdown }) {
  const entries = Object.entries(breakdown || {}).filter(([, count]) => count > 0);
  if (entries.length === 0) {
    return null;
  }

  return (
    <section className="topic-breakdown" aria-label="Topic breakdown">
      <span>Today:</span>
      {entries.map(([topic, count]) => (
        <span key={topic}>
          {count} {topic}
        </span>
      ))}
    </section>
  );
}
