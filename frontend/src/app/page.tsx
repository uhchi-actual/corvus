const phaseItems = [
  "Baseline SQL",
  "Fuel-trim drift",
  "DTC correlation",
  "Health score"
];

export default function Home() {
  return (
    <main className="shell" aria-label="Corvus Phase 2">
      <section className="console" aria-labelledby="corvus-title">
        <p className="kicker">phase 2</p>
        <h1 id="corvus-title" className="wordmark" data-text="corvus">
          corvus
        </h1>
        <p className="statement">
          Deterministic SQL analysis over seeded OBD-II telemetry.
        </p>
        <div className="statusRow" aria-label="Phase 2 scope">
          {phaseItems.map((item) => (
            <span key={item}>{item}</span>
          ))}
        </div>
      </section>
    </main>
  );
}
