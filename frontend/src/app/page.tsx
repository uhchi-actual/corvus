const phaseItems = [
  "CSV ingest",
  "Emulator ingest",
  "Live ELM327 read-only",
  "Seeded SQLite"
];

export default function Home() {
  return (
    <main className="shell" aria-label="Corvus Phase 1">
      <section className="console" aria-labelledby="corvus-title">
        <p className="kicker">phase 1</p>
        <h1 id="corvus-title" className="wordmark" data-text="corvus">
          corvus
        </h1>
        <p className="statement">
          Read-only diagnostic intelligence, staged for deterministic SQL analysis.
        </p>
        <div className="statusRow" aria-label="Phase 1 scope">
          {phaseItems.map((item) => (
            <span key={item}>{item}</span>
          ))}
        </div>
      </section>
    </main>
  );
}
