import { useState } from "react";
import type { QueryResult, GenieStatus } from "../types";
import ResultChart, { pickChartType } from "./ResultChart";

type Tab = "chart" | "table" | "sql";

interface Props {
  gs: GenieStatus;
  elapsed: string | null;
  onRetry?: () => void;
}

function copySql(sql: string) {
  navigator.clipboard.writeText(sql);
}

function exportCsv(result: QueryResult) {
  const header = result.columns.map((c) => c.name).join(",");
  const rows = result.rows.map((r) =>
    r.map((cell) => {
      const s = cell ?? "";
      return s.includes(",") || s.includes('"') || s.includes("\n")
        ? `"${s.replace(/"/g, '""')}"`
        : s;
    }).join(",")
  );
  const csv = [header, ...rows].join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "genie_result.csv";
  a.click();
  URL.revokeObjectURL(url);
}

export default function ResultCard({ gs, elapsed, onRetry }: Props) {
  const hasResult = gs.result && gs.result.rows.length > 0;
  const chartType = hasResult ? pickChartType(gs.result!) : null;
  const defaultTab: Tab = chartType ? "chart" : "table";
  const [activeTab, setActiveTab] = useState<Tab>(defaultTab);
  const [copiedSql, setCopiedSql] = useState(false);
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null);

  const handleCopySql = () => {
    if (gs.sql) {
      copySql(gs.sql);
      setCopiedSql(true);
      setTimeout(() => setCopiedSql(false), 2000);
    }
  };

  // Error state
  if (gs.status === "FAILED") {
    return (
      <section className="result-card">
        <div className="result-card-body" style={{ padding: 20 }}>
          <p style={{ color: "var(--negative)", margin: 0, fontSize: 15 }}>{gs.error}</p>
          {onRetry && (
            <button className="result-action-btn" onClick={onRetry} style={{ marginTop: 12 }}>
              Retry
            </button>
          )}
        </div>
        {gs.sql && <SqlBlock sql={gs.sql} />}
      </section>
    );
  }

  // Empty result
  if (gs.result && gs.result.rows.length === 0) {
    return (
      <section className="result-card">
        <div className="result-card-body" style={{ padding: 20 }}>
          <p style={{ color: "var(--muted)", margin: 0, fontSize: 15 }}>
            The query ran successfully but returned no rows.
          </p>
        </div>
        {gs.sql && <SqlBlock sql={gs.sql} />}
        <ResultFooter gs={gs} elapsed={elapsed} onCopySql={handleCopySql} copiedSql={copiedSql}
          feedback={feedback} onFeedback={setFeedback} />
      </section>
    );
  }

  return (
    <section className="result-card">
      {/* Header with title + tabs */}
      <div className="result-card-header">
        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <span className="result-title">Query result</span>
          {gs.result && (
            <span className="result-subtitle">
              {gs.result.row_count} row{gs.result.row_count !== 1 ? "s" : ""}
              {gs.result.truncated && ` (showing first ${gs.result.rows.length})`}
            </span>
          )}
        </div>
        <div className="tab-group">
          {chartType && (
            <button className={`tab-btn ${activeTab === "chart" ? "active" : ""}`}
              onClick={() => setActiveTab("chart")}>Chart</button>
          )}
          <button className={`tab-btn ${activeTab === "table" ? "active" : ""}`}
            onClick={() => setActiveTab("table")}>Table</button>
          <button className={`tab-btn ${activeTab === "sql" ? "active" : ""}`}
            onClick={() => setActiveTab("sql")}>SQL</button>
        </div>
      </div>

      {/* Tab content */}
      <div className="result-card-body">
        {activeTab === "chart" && gs.result && chartType && (
          <div style={{ padding: 20 }}>
            <ResultChart result={gs.result} chartType={chartType} />
          </div>
        )}

        {activeTab === "table" && gs.result && (
          <div style={{ overflowX: "auto" }}>
            <table className="result-table">
              <thead>
                <tr>
                  {gs.result.columns.map((col) => (
                    <th key={col.name}>{col.name}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {gs.result.rows.slice(0, 100).map((row, ri) => (
                  <tr key={ri}>
                    {row.map((cell, ci) => (
                      <td key={ci}>{cell}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === "sql" && gs.sql && <SqlBlock sql={gs.sql} />}
      </div>

      {/* Footer */}
      <ResultFooter
        gs={gs} elapsed={elapsed}
        onCopySql={handleCopySql} copiedSql={copiedSql}
        onExportCsv={gs.result ? () => exportCsv(gs.result!) : undefined}
        feedback={feedback} onFeedback={setFeedback}
      />
    </section>
  );
}

function SqlBlock({ sql }: { sql: string }) {
  return (
    <div className="sql-block">
      <div className="sql-block-header">
        <span>SQL generated by Genie</span>
        <span>Databricks SQL</span>
      </div>
      <pre className="sql-block-code">{sql}</pre>
    </div>
  );
}

function ResultFooter({
  gs, elapsed, onCopySql, copiedSql, onExportCsv, feedback, onFeedback,
}: {
  gs: GenieStatus;
  elapsed: string | null;
  onCopySql: () => void;
  copiedSql: boolean;
  onExportCsv?: () => void;
  feedback: "up" | "down" | null;
  onFeedback: (v: "up" | "down") => void;
}) {
  return (
    <div className="result-footer">
      <span>
        {gs.tables_used.length > 0 && gs.tables_used.join(", ")}
        {gs.result && <> &middot; {gs.result.row_count} rows</>}
        {elapsed && <> &middot; {elapsed} s</>}
      </span>
      <div className="result-actions">
        <button
          className={`result-icon-btn ${feedback === "up" ? "active-feedback" : ""}`}
          aria-label="Good answer"
          onClick={() => onFeedback("up")}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill={feedback === "up" ? "var(--accent)" : "none"}
            stroke={feedback === "up" ? "var(--accent)" : "#15181C"} strokeWidth="2"
            strokeLinecap="round" strokeLinejoin="round">
            <path d="M7 11v9H4v-9h3zm0 0 4-8c1.7 0 3 1.3 3 3v3h5.5a2 2 0 0 1 2 2.3l-1.2 7a2 2 0 0 1-2 1.7H7" />
          </svg>
        </button>
        <button
          className={`result-icon-btn ${feedback === "down" ? "active-feedback" : ""}`}
          aria-label="Bad answer"
          onClick={() => onFeedback("down")}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill={feedback === "down" ? "var(--negative)" : "none"}
            stroke={feedback === "down" ? "var(--negative)" : "#15181C"} strokeWidth="2"
            strokeLinecap="round" strokeLinejoin="round">
            <path d="M17 13V4h3v9h-3zm0 0-4 8c-1.7 0-3-1.3-3-3v-3H4.5a2 2 0 0 1-2-2.3l1.2-7a2 2 0 0 1 2-1.7H17" />
          </svg>
        </button>
        <button className="result-action-btn" onClick={onCopySql}>
          {copiedSql ? "Copied!" : "Copy SQL"}
        </button>
        {onExportCsv && (
          <button className="result-action-btn" onClick={onExportCsv}>
            Export CSV
          </button>
        )}
      </div>
    </div>
  );
}
