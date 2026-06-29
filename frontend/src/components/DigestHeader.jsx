import React from "react";

export default function DigestHeader({ date, count }) {
  const formatted = new Intl.DateTimeFormat(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric"
  }).format(new Date(`${date}T12:00:00`));

  return (
    <header className="digest-header">
      <div>
        <p className="date-label">{formatted}</p>
        <h1>Khabar</h1>
        <p className="tagline">Your news. No noise.</p>
      </div>
      <p className="article-count">{count} stories</p>
    </header>
  );
}
