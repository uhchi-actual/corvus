import type { TraceStep } from "../../types/dashboard";

type AgentProfile = {
  name: string;
  tagline: string;
  role: string;
};

type Props = {
  profile: AgentProfile;
  steps: TraceStep[];
};

export function AgentPanel({ profile, steps }: Props) {
  return (
    <article className="panel agentPanel flowIn delayedFive">
      <div className="panelHead">
        <p>{profile.tagline}</p>
        <h2>{profile.name}</h2>
      </div>
      <p className="agentRole">{profile.role}</p>
      <ol className="agentSteps">
        {steps.map((step) => (
          <li key={`${step.node}-${step.summary}`}>
            <strong>{step.title ?? step.node}</strong>
            <p>{step.body ?? step.summary}</p>
          </li>
        ))}
      </ol>
    </article>
  );
}
