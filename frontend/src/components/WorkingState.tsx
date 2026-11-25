import { CheckIcon } from "./Icons";

const STEPS = [
  { key: "read", label: "Read your question", after: ["SUBMITTED"] },
  { key: "tables", label: "Found the tables it needs", after: ["FETCHING_METADATA", "FILTERING_CONTEXT"] },
  { key: "sql", label: "Writing the SQL", after: ["ASKING_AI"] },
  { key: "run", label: "Running it on the SQL warehouse", after: ["PENDING_WAREHOUSE", "EXECUTING_QUERY"] },
  { key: "summary", label: "Writing the summary", after: ["COMPLETED"] },
];

// Map Genie status to which step index is currently active
function activeStepIndex(status: string): number {
  for (let i = STEPS.length - 1; i >= 0; i--) {
    if (STEPS[i].after.includes(status)) return i;
  }
  return 0;
}

interface Props {
  status: string;
  tablesUsed?: string[];
}

export default function WorkingState({ status, tablesUsed }: Props) {
  const active = activeStepIndex(status);

  return (
    <section className="working-card">
      <div className="working-header">
        <span>Genie is working on it</span>
      </div>

      <ol className="step-list">
        {STEPS.map((step, i) => {
          const isDone = i < active || (i === active && status === "COMPLETED");
          const isActive = i === active && status !== "COMPLETED";
          const isPending = i > active;

          return (
            <li key={step.key} className={`step-item ${step.key === "tables" && tablesUsed?.length ? "has-detail" : ""}`}>
              <span className={`step-icon ${isDone ? "done" : isActive ? "active" : "pending"}`}>
                {isDone && <CheckIcon />}
              </span>
              <span style={{
                display: "flex", flexDirection: "column", gap: 6,
                fontWeight: isActive ? 500 : 400,
                color: isPending ? "var(--muted)" : "var(--ink)",
              }}>
                <span>{step.label}</span>
                {step.key === "tables" && isDone && tablesUsed && tablesUsed.length > 0 && (
                  <span className="step-tables">
                    {tablesUsed.map((t) => (
                      <span key={t} className="step-table-chip">{t}</span>
                    ))}
                  </span>
                )}
              </span>
            </li>
          );
        })}
      </ol>

      <div className="skeleton-lines">
        <div className="skeleton-line" style={{ width: "100%" }} />
        <div className="skeleton-line" style={{ width: "82%" }} />
        <div className="skeleton-line" style={{ width: "64%" }} />
      </div>

      <span className="working-note">
        Some questions take a minute. You can leave this chat and the answer will be here when you come back.
      </span>
    </section>
  );
}
