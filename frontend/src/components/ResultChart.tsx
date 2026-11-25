import { useState, useRef } from "react";
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import type { QueryResult } from "../types";

export type ChartType = "bar" | "line" | "stacked-bar" | "heatmap" | null;

const NUMERIC_TYPES = new Set(["INT", "LONG", "BIGINT", "DOUBLE", "FLOAT", "DECIMAL", "SHORT", "TINYINT"]);

function isNumericCol(type: string): boolean {
  return NUMERIC_TYPES.has(type.toUpperCase());
}

function looksLikeDate(name: string, values: string[]): boolean {
  const n = name.toLowerCase();
  if (n.includes("date") || n.includes("year") || n.includes("month") || n.includes("quarter")) return true;
  const sample = values.slice(0, 5);
  return sample.every((v) => /^\d{4}/.test(v));
}

function sumsToAbout100(rows: string[][], numericIndices: number[]): boolean {
  if (numericIndices.length < 2 || rows.length < 2) return false;
  let matchCount = 0;
  for (const row of rows) {
    const sum = numericIndices.reduce((acc, i) => acc + (parseFloat(row[i]) || 0), 0);
    if (sum >= 90 && sum <= 110) matchCount++;
  }
  return matchCount >= rows.length * 0.7;
}

/** Deduplicate and sort smartly: numeric/grade-like values sorted numerically, rest alphabetically */
function uniqueSorted(values: string[]): string[] {
  const unique = [...new Set(values)];
  return unique.sort((a, b) => {
    const na = parseGrade(a);
    const nb = parseGrade(b);
    if (na !== null && nb !== null) return na - nb;
    if (na !== null) return -1;
    if (nb !== null) return 1;
    return a.localeCompare(b);
  });
}

function parseGrade(v: string): number | null {
  const u = v.trim().toUpperCase();
  if (u === "PK" || u === "PRE-K" || u === "P4") return -1;
  if (u === "KG" || u === "K" || u === "KINDERGARTEN") return 0;
  const n = parseFloat(u);
  if (!isNaN(n)) return n;
  return null;
}

export function pickChartType(result: QueryResult): ChartType {
  const { columns, rows } = result;
  if (rows.length === 0 || columns.length < 2) return null;

  const numericIndices = columns
    .map((c, i) => ({ ...c, idx: i }))
    .filter((c) => isNumericCol(c.type))
    .map((c) => c.idx);

  const categoryIndices = columns
    .map((_, i) => i)
    .filter((i) => !numericIndices.includes(i));

  if (categoryIndices.length === 0 || numericIndices.length === 0) return null;

  // Heatmap: 2+ category columns + numeric columns
  if (categoryIndices.length >= 2 && numericIndices.length >= 1) {
    return "heatmap";
  }

  const catIdx = categoryIndices[0];
  const catValues = rows.map((r) => r[catIdx]);

  // Stacked bar: shares summing to ~100
  if (numericIndices.length >= 2 && sumsToAbout100(rows, numericIndices)) {
    return "stacked-bar";
  }

  // Line chart: date/time column + numbers
  if (looksLikeDate(columns[catIdx].name, catValues) && numericIndices.length >= 1) {
    return "line";
  }

  // Bar chart: one category + 1-3 numbers
  if (categoryIndices.length >= 1 && numericIndices.length >= 1 && numericIndices.length <= 3) {
    return "bar";
  }

  return null;
}

const COLORS = ["#0B6E6E", "#7DA7A3", "#C9CDD2", "#5A606A"];

interface Props {
  result: QueryResult;
  chartType: ChartType;
}

export default function ResultChart({ result, chartType }: Props) {
  const { columns, rows } = result;

  const numericIndices = columns
    .map((c, i) => ({ ...c, idx: i }))
    .filter((c) => isNumericCol(c.type))
    .map((c) => c.idx);
  const categoryIndices = columns
    .map((_, i) => i)
    .filter((i) => !numericIndices.includes(i));

  if (chartType === "heatmap") {
    return <Heatmap columns={columns} rows={rows} categoryIndices={categoryIndices} numericIndices={numericIndices} />;
  }

  const categoryIdx = categoryIndices[0];

  const data = rows.map((row) => {
    const obj: Record<string, string | number> = {};
    obj[columns[categoryIdx].name] = row[categoryIdx];
    for (const ni of numericIndices) {
      obj[columns[ni].name] = parseFloat(row[ni]) || 0;
    }
    return obj;
  });

  const catKey = columns[categoryIdx].name;
  const numKeys = numericIndices.map((i) => columns[i].name);

  if (chartType === "bar" || chartType === "stacked-bar") {
    return (
      <ResponsiveContainer width="100%" height={Math.min(rows.length * 48 + 60, 500)}>
        <BarChart data={data} layout="horizontal" margin={{ top: 5, right: 20, bottom: 5, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E3E3DD" />
          <XAxis dataKey={catKey} tick={{ fontSize: 12, fill: "#5A606A" }} />
          <YAxis tick={{ fontSize: 12, fill: "#5A606A" }} />
          <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid #E3E3DD", fontSize: 13 }} />
          <Legend wrapperStyle={{ fontSize: 13 }} />
          {numKeys.map((key, i) => (
            <Bar
              key={key} dataKey={key} fill={COLORS[i % COLORS.length]}
              stackId={chartType === "stacked-bar" ? "stack" : undefined}
              radius={chartType === "stacked-bar" ? undefined : [4, 4, 0, 0]}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    );
  }

  if (chartType === "line") {
    return (
      <ResponsiveContainer width="100%" height={340}>
        <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E3E3DD" />
          <XAxis dataKey={catKey} tick={{ fontSize: 12, fill: "#5A606A" }} />
          <YAxis tick={{ fontSize: 12, fill: "#5A606A" }} />
          <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid #E3E3DD", fontSize: 13 }} />
          <Legend wrapperStyle={{ fontSize: 13 }} />
          {numKeys.map((key, i) => (
            <Line
              key={key} type="monotone" dataKey={key}
              stroke={COLORS[i % COLORS.length]} strokeWidth={2} dot={{ r: 3 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    );
  }

  return null;
}

// ── Heatmap ──────────────────────────────────────────────────────────────

interface HeatmapProps {
  columns: QueryResult["columns"];
  rows: string[][];
  categoryIndices: number[];
  numericIndices: number[];
}

function interpolateColor(t: number): string {
  const r = Math.round(227 + (11 - 227) * t);
  const g = Math.round(241 + (110 - 241) * t);
  const b = Math.round(240 + (110 - 240) * t);
  return `rgb(${r},${g},${b})`;
}

function fmt(v: number): string {
  if (v % 1 === 0) return String(v);
  return v.toFixed(1);
}

interface TooltipData {
  rowLabel: string;
  colLabel: string;
  values: { name: string; value: string }[];
  x: number;
  y: number;
}

function Heatmap({ columns, rows, categoryIndices, numericIndices }: HeatmapProps) {
  const [colorByIdx, setColorByIdx] = useState(0);
  const [tooltip, setTooltip] = useState<TooltipData | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const colorNumIdx = numericIndices[colorByIdx] ?? numericIndices[0];
  const colorName = columns[colorNumIdx].name;

  const rowIdx = categoryIndices[0];
  const colIdx = categoryIndices[1];
  const rowName = columns[rowIdx].name;
  const colName = columns[colIdx].name;

  const rowValues = uniqueSorted(rows.map((r) => r[rowIdx]));
  const colValues = uniqueSorted(rows.map((r) => r[colIdx]));

  // Build lookup
  const lookup = new Map<string, string[]>();
  let minVal = Infinity, maxVal = -Infinity;
  for (const row of rows) {
    const key = `${row[rowIdx]}|${row[colIdx]}`;
    const val = parseFloat(row[colorNumIdx]) || 0;
    lookup.set(key, row);
    if (val < minVal) minVal = val;
    if (val > maxVal) maxVal = val;
  }
  const range = maxVal - minVal || 1;

  const handleMouseEnter = (rv: string, cv: string, e: React.MouseEvent) => {
    const row = lookup.get(`${rv}|${cv}`);
    if (!row || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    setTooltip({
      rowLabel: rv,
      colLabel: cv,
      values: numericIndices.map((ni) => ({
        name: columns[ni].name,
        value: row[ni],
      })),
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  };

  return (
    <div className="heatmap-container" ref={containerRef}>
      {/* Controls: metric selector + legend */}
      <div className="heatmap-controls">
        {numericIndices.length > 1 && (
          <div className="heatmap-metric-picker">
            <span className="heatmap-picker-label">Color by</span>
            <select
              value={colorByIdx}
              onChange={(e) => setColorByIdx(Number(e.target.value))}
              className="heatmap-select"
            >
              {numericIndices.map((ni, i) => (
                <option key={ni} value={i}>{columns[ni].name}</option>
              ))}
            </select>
          </div>
        )}
        <div className="heatmap-legend">
          <span className="heatmap-legend-label">{colorName}</span>
          <div className="heatmap-gradient">
            <span>{fmt(minVal)}</span>
            <div className="heatmap-gradient-bar" />
            <span>{fmt(maxVal)}</span>
          </div>
        </div>
      </div>

      <div className="heatmap-scroll">
        <table className="heatmap-table">
          <thead>
            <tr>
              <th className="heatmap-corner">{rowName} \ {colName}</th>
              {colValues.map((c) => (
                <th key={c} className="heatmap-col-header">{c}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rowValues.map((rv) => (
              <tr key={rv}>
                <th className="heatmap-row-header">{rv}</th>
                {colValues.map((cv) => {
                  const row = lookup.get(`${rv}|${cv}`);
                  if (!row) {
                    return <td key={cv} className="heatmap-cell heatmap-empty">—</td>;
                  }
                  const val = parseFloat(row[colorNumIdx]) || 0;
                  const t = (val - minVal) / range;
                  const bg = interpolateColor(t);
                  const textColor = t > 0.55 ? "#FFFFFF" : "#15181C";

                  return (
                    <td
                      key={cv}
                      className="heatmap-cell"
                      style={{ backgroundColor: bg, color: textColor }}
                      onMouseEnter={(e) => handleMouseEnter(rv, cv, e)}
                      onMouseMove={(e) => {
                        if (!containerRef.current) return;
                        const rect = containerRef.current.getBoundingClientRect();
                        setTooltip((prev) => prev ? { ...prev, x: e.clientX - rect.left, y: e.clientY - rect.top } : null);
                      }}
                      onMouseLeave={() => setTooltip(null)}
                    >
                      {numericIndices.map((ni, i) => (
                        <span key={ni} className={i === 0 ? "heatmap-value" : "heatmap-secondary"}>
                          {fmt(parseFloat(row[ni]) || 0)}{columns[ni].name.includes("pct") || columns[ni].name.includes("percent") || columns[ni].name.includes("rate") || columns[ni].name.includes("share") ? "%" : ""}
                        </span>
                      ))}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Floating tooltip */}
      {tooltip && (
        <div
          className="heatmap-tooltip"
          style={{ left: tooltip.x + 12, top: tooltip.y - 8 }}
        >
          <div className="heatmap-tooltip-header">
            {rowName}: <strong>{tooltip.rowLabel}</strong> &nbsp;·&nbsp; {colName}: <strong>{tooltip.colLabel}</strong>
          </div>
          {tooltip.values.map((v) => (
            <div key={v.name} className="heatmap-tooltip-row">
              <span className="heatmap-tooltip-name">{v.name}</span>
              <span className="heatmap-tooltip-val">{v.value}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
