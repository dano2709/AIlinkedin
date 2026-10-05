export default function Home() {
  const stages = [
    "Search",
    "Discover",
    "Normalize",
    "Filter",
    "Analyze",
    "Rank",
    "Notify",
  ];

  return (
    <main>
      <header className="hero">
        <span className="eyebrow">AIlinkedin</span>
        <h1>Job Intelligence</h1>
        <p>
          Discover, evaluate and track high-value job opportunities through a
          provider-neutral pipeline.
        </p>
      </header>

      <section className="stats" aria-label="Overview">
        <article className="card">
          <span>Jobs</span>
          <strong>0</strong>
          <small>Foundation ready</small>
        </article>
        <article className="card">
          <span>Strong matches</span>
          <strong>0</strong>
          <small>AI scoring comes later</small>
        </article>
        <article className="card">
          <span>Searches</span>
          <strong>0</strong>
          <small>Search management comes next</small>
        </article>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">Architecture</span>
            <h2>Processing pipeline</h2>
          </div>
          <span className="status">Foundation</span>
        </div>

        <div className="pipeline">
          {stages.map((stage, index) => (
            <div className="stage" key={stage}>
              <span className="stage-index">{String(index + 1).padStart(2, "0")}</span>
              <span>{stage}</span>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
