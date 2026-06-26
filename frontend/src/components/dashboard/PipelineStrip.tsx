import type { PipelineModule } from "../../types/dashboard";

type Props = {
  modules: PipelineModule[];
};

export function PipelineStrip({ modules }: Props) {
  return (
    <section className="panel pipelinePanel flowIn" aria-label="Corvus modular pipeline">
      <div className="panelHead">
        <p>Five modules</p>
        <h2>How Corvus fits together</h2>
      </div>
      <p className="guideCopy">
        Each box is a separate step. SQL owns the numbers. Huginn and Muninn only explain
        what SQL already computed.
      </p>
      <ol className="pipelineStrip">
        {modules.map((module, index) => (
          <li className="pipelineModule" key={module.id}>
            <div className="pipelineIndex">{index + 1}</div>
            <div className="pipelineBody">
              <div className="pipelineMeta">
                <span className="pipelineOwner">{module.owner}</span>
                <strong>{module.title}</strong>
              </div>
              <p>{module.body}</p>
              <dl className="pipelineIo">
                <div>
                  <dt>In</dt>
                  <dd>{module.input}</dd>
                </div>
                <div>
                  <dt>Out</dt>
                  <dd>{module.output}</dd>
                </div>
              </dl>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
