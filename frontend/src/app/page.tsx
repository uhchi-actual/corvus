const phaseItems = [
  "Scaffold",
  "Read-only OBD-II scope",
  "SQL-first analysis",
  "Huginn / Muninn reserved"
];

export default function Home() {
  return (
    <main className="shell" aria-label="Corvus Phase 0">
      <section className="console" aria-labelledby="corvus-title">
        <p className="kicker">phase 0</p>
        <h1 id="corvus-title" className="wordmark">
          corvus
        </h1>
        <p className="statement">
          Read-only diagnostic intelligence, staged for deterministic SQL analysis.
        </p>
        <div className="statusRow" aria-label="Phase 0 scope">
          {phaseItems.map((item) => (
            <span key={item}>{item}</span>
          ))}
        </div>
      </section>
    </main>
  );
}

