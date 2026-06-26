import type { SqlModule } from "../../types/dashboard";

type Props = {
  modules: SqlModule[];
  sessionLabel: string;
};

export function SqlModuleGrid({ modules, sessionLabel }: Props) {
  return (
    <section className="panel sqlModulePanel flowIn delayedTwo" aria-label="SQL modules">
      <div className="panelHead">
        <p>SQL owns the math</p>
        <h2>Query modules for {sessionLabel}</h2>
      </div>
      <p className="guideCopy">
        Each card maps to a file in <code>data/queries/</code>. The dashboard never invents
        sensor values.
      </p>
      <div className="sqlModuleGrid">
        {modules.map((module) => (
          <article className="sqlModuleCard" key={module.id}>
            <header>
              <span>{module.owner}</span>
              <strong>{module.title}</strong>
              <code>{module.query}</code>
            </header>
            <p>{module.body}</p>
            <dl>
              <div>
                <dt>Input</dt>
                <dd>{module.input}</dd>
              </div>
              <div>
                <dt>SQL result</dt>
                <dd>{module.output}</dd>
              </div>
            </dl>
          </article>
        ))}
      </div>
    </section>
  );
}
