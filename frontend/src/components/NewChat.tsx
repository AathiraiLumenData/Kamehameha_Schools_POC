const STARTERS = [
  { label: "Outcomes", text: "What share of students admitted in each school year are still enrolled or have graduated?" },
  { label: "SAT", text: "What is the average latest SAT total and percent meeting the math benchmark by campus?" },
  { label: "Enrollment", text: "What are the main grade levels and school years covered in the enrollment data?" },
  { label: "Overview", text: "Summarize the datasets in this space" },
];

import type { SpaceInfo } from "../types";

interface Props {
  onAsk: (question: string) => void;
  spaceInfo: SpaceInfo | null;
}

export default function NewChat({ onAsk, spaceInfo }: Props) {
  return (
    <div className="new-chat">
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        <h1>{spaceInfo?.space_name || "What do you want to know?"}</h1>
        <p className="subtitle">
          Ask a question in plain English and get back a summary, chart, and the SQL behind it.
        </p>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <span style={{ fontSize: 13, fontWeight: 500, color: "var(--muted)" }}>Try one of these</span>
        <div className="starter-grid">
          {STARTERS.map((s) => (
            <button key={s.label} className="starter-card" onClick={() => onAsk(s.text)}>
              <span className="label">{s.label}</span>
              <span className="text">{s.text}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
