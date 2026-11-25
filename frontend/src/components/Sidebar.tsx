import { DbIcon, PlusIcon } from "./Icons";
import type { Conversation, SpaceInfo } from "../types";

interface Props {
  conversations: Conversation[];
  activeId: string | null;
  onNewChat: () => void;
  onSelect: (id: string) => void;
  onSignOut?: () => void;
  onOpenSpace?: () => void;
  spaceInfo: SpaceInfo | null;
  className?: string;
}

export default function Sidebar({ conversations, activeId, onNewChat, onSelect, onSignOut, onOpenSpace, spaceInfo, className }: Props) {
  const recent = conversations.filter((c) => c.id);

  const spaceName = spaceInfo?.space_name ?? "Loading…";
  const tableCount = spaceInfo?.tables.length ?? 0;

  return (
    <aside className={`sidebar ${className || ""}`}>
      <div className="sidebar-brand">
        <div className="icon-box"><DbIcon /></div>
        <span>Ask your data</span>
      </div>

      <button className="btn-new-chat" onClick={onNewChat}>
        <PlusIcon /> New chat
      </button>

      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        <span className="sidebar-section-label">Genie space</span>
        <button className="space-card" onClick={onOpenSpace}>
          <span style={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <span className="space-name">{spaceName}</span>
            <span className="space-meta">
              Databricks Genie{tableCount > 0 ? ` · ${tableCount} datasets` : ""}
            </span>
          </span>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#5A606A" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
            <polyline points="15 3 21 3 21 9" />
            <line x1="10" y1="14" x2="21" y2="3" />
          </svg>
        </button>
      </div>

      {recent.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <span className="sidebar-section-label" style={{ paddingBottom: 6 }}>Recent</span>
          <div className="recent-list">
            {recent.map((c) => (
              <button
                key={c.id}
                className={`recent-item ${c.id === activeId ? "active" : ""}`}
                onClick={() => c.id && onSelect(c.id)}
              >
                {c.title}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="sidebar-user">
        <div className="user-avatar">U</div>
        <div style={{ display: "flex", flexDirection: "column", flex: 1 }}>
          <span className="name">User</span>
          <span className="meta">Signed in with Databricks</span>
        </div>
        {onSignOut && (
          <button onClick={onSignOut} className="sign-out-btn" aria-label="Sign out" title="Sign out">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
          </button>
        )}
      </div>
    </aside>
  );
}
