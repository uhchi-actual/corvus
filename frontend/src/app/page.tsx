export default function Home() {
  return (
    <main className="shell" aria-label="Corvus">
      <section className="console" aria-labelledby="corvus-title">
        <h1 id="corvus-title" className="wordmark" data-text="corvus">
          corvus
        </h1>
        <p className="statement">OBD-II telemetry analyzed in SQL</p>
        <p className="sourceLine">
          Data:{" "}
          <a href="https://doi.org/10.35097/1130">KIT/RADAR OBD-II</a>
          {" / "}
          <a href="https://creativecommons.org/licenses/by/4.0/deed.en">
            CC BY 4.0
          </a>
        </p>
      </section>
    </main>
  );
}
