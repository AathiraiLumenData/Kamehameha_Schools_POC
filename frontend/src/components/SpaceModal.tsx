import type { SpaceInfo, TableInfo } from "../types";
import { DbIcon } from "./Icons";

interface Props {
  spaceInfo: SpaceInfo;
  onClose: () => void;
}

function TableRow({ t, icon }: { t: TableInfo; icon: React.ReactNode }) {
  return (
    <div className="modal-table-item">
      <div className="modal-table-icon">{icon}</div>
      <div className="modal-table-info">
        <div className="modal-table-top">
          <code>{t.name}</code>
          <span className="modal-table-cols">{t.column_count} cols</span>
        </div>
        {t.comment && <span className="modal-table-comment">{t.comment}</span>}
      </div>
    </div>
  );
}

const tableIcon = (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="18" height="18" rx="2" />
    <path d="M3 9h18M3 15h18M9 3v18" />
  </svg>
);

const viewIcon = (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--chart-2)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
    <circle cx="12" cy="12" r="3" />
  </svg>
);

export default function SpaceModal({ spaceInfo, onClose }: Props) {
  const tables = spaceInfo.tables.filter((t) => t.type === "MANAGED" || t.type === "TABLE" || t.type === "EXTERNAL");
  const views = spaceInfo.tables.filter((t) => t.type !== "MANAGED" && t.type !== "TABLE" && t.type !== "EXTERNAL");

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-header-left">
            <div className="modal-icon"><DbIcon size={20} /></div>
            <div>
              <h2 className="modal-title">{spaceInfo.space_name}</h2>
              <span className="modal-subtitle">Databricks Genie Space</span>
            </div>
          </div>
          <button className="modal-close" onClick={onClose} aria-label="Close">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {spaceInfo.catalog && (
          <div className="modal-meta-row">
            <span className="modal-meta-label">Catalog</span>
            <code className="modal-meta-value">{spaceInfo.catalog}</code>
          </div>
        )}

        <div className="modal-meta-row">
          <span className="modal-meta-label">Datasets</span>
          <span className="modal-meta-value">{spaceInfo.tables.length} total</span>
        </div>

        {tables.length > 0 && (
          <div className="modal-section">
            <span className="modal-section-label">Tables ({tables.length})</span>
            <div className="modal-table-list">
              {tables.map((t) => <TableRow key={t.name} t={t} icon={tableIcon} />)}
            </div>
          </div>
        )}

        {views.length > 0 && (
          <div className="modal-section">
            <span className="modal-section-label">Metric Views ({views.length})</span>
            <div className="modal-table-list">
              {views.map((t) => <TableRow key={t.name} t={t} icon={viewIcon} />)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
