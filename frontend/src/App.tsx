import { useState, useCallback, useRef, useEffect } from "react";
import "./App.css";
import type { Conversation, Message, GenieStatus, SpaceInfo } from "./types";
import { ask, pollStatus, getStoredToken, fetchSpaceInfo, clearToken } from "./api";
import Sidebar from "./components/Sidebar";
import Composer from "./components/Composer";
import NewChat from "./components/NewChat";
import WorkingState from "./components/WorkingState";
import TokenPrompt from "./components/TokenPrompt";
import ResultCard from "./components/ResultCard";
import SpaceModal from "./components/SpaceModal";
import Markdown from "react-markdown";
import { DbIcon, PlusIcon, MenuIcon } from "./components/Icons";

const POLL_INTERVAL = 1500;
const FINAL = new Set(["COMPLETED", "FAILED", "CANCELLED"]);

function newConversation(): Conversation {
  return { id: null, title: "New chat", messages: [] };
}

export default function App() {
  const [hasToken, setHasToken] = useState(() => !!getStoredToken());
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeIdx, setActiveIdx] = useState<number | null>(null);
  const [polling, setPolling] = useState(false);
  const [currentGenieStatus, setCurrentGenieStatus] = useState<string>("SUBMITTED");
  const [currentTablesUsed, setCurrentTablesUsed] = useState<string[]>([]);
  const [spaceInfo, setSpaceInfo] = useState<SpaceInfo | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [spaceModalOpen, setSpaceModalOpen] = useState(false);
  const pollRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const active = activeIdx !== null ? conversations[activeIdx] : null;

  const scrollToBottom = useCallback(() => {
    setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
  }, []);

  // Fetch space info on login
  useEffect(() => {
    if (hasToken && !spaceInfo) {
      fetchSpaceInfo()
        .then(setSpaceInfo)
        .catch((err) => {
          if (err instanceof Error && err.message === "AUTH_EXPIRED") setHasToken(false);
        });
    }
  }, [hasToken, spaceInfo]);

  // Clean up polling on unmount
  useEffect(() => {
    return () => { if (pollRef.current) clearTimeout(pollRef.current); };
  }, []);

  const updateConversation = useCallback((idx: number, updater: (c: Conversation) => Conversation) => {
    setConversations((prev) => prev.map((c, i) => (i === idx ? updater(c) : c)));
  }, []);

  const handleAsk = useCallback(async (question: string) => {
    // Create or reuse conversation
    let idx = activeIdx;
    if (idx === null || conversations[idx]?.messages.length > 0) {
      const c = newConversation();
      c.title = question.length > 50 ? question.slice(0, 50) + "…" : question;
      setConversations((prev) => [...prev, c]);
      idx = conversations.length;
      setActiveIdx(idx);
    } else {
      updateConversation(idx, (c) => ({
        ...c,
        title: question.length > 50 ? question.slice(0, 50) + "…" : question,
      }));
    }

    const userMsg: Message = { id: crypto.randomUUID(), role: "user", content: question };
    const assistantMsg: Message = { id: crypto.randomUUID(), role: "assistant", content: "", startedAt: Date.now() };

    updateConversation(idx, (c) => ({
      ...c,
      messages: [...c.messages, userMsg, assistantMsg],
    }));
    setPolling(true);
    setCurrentGenieStatus("SUBMITTED");
    setCurrentTablesUsed([]);
    scrollToBottom();

    try {
      const convId = conversations[idx]?.id ?? null;
      const { conversation_id, message_id } = await ask(question, convId);

      // Store conversation_id
      updateConversation(idx, (c) => ({ ...c, id: conversation_id }));

      // Start polling
      const doPoll = async () => {
        try {
          const result: GenieStatus = await pollStatus(conversation_id, message_id);
          setCurrentGenieStatus(result.status);
          if (result.tables_used?.length) {
            setCurrentTablesUsed(result.tables_used);
          }

          if (FINAL.has(result.status)) {
            setPolling(false);
            updateConversation(idx!, (c) => ({
              ...c,
              messages: c.messages.map((m) =>
                m.id === assistantMsg.id
                  ? { ...m, content: result.text || "", genieStatus: result, completedAt: Date.now() }
                  : m
              ),
            }));
            scrollToBottom();
          } else {
            pollRef.current = setTimeout(doPoll, POLL_INTERVAL);
          }
        } catch (err: unknown) {
          setPolling(false);
          const message = err instanceof Error && err.message === "AUTH_EXPIRED"
            ? "Your token has expired. Please sign in again."
            : "Something went wrong while waiting for Genie.";
          updateConversation(idx!, (c) => ({
            ...c,
            messages: c.messages.map((m) =>
              m.id === assistantMsg.id
                ? { ...m, content: message, genieStatus: { status: "FAILED", error: message, text: null, description: null, sql: null, statement_id: null, attachment_id: null, result: null, tables_used: [], suggested_questions: [] } }
                : m
            ),
          }));
          if (err instanceof Error && err.message === "AUTH_EXPIRED") {
            setHasToken(false);
          }
        }
      };
      doPoll();
    } catch (err: unknown) {
      setPolling(false);
      const message = err instanceof Error && err.message === "AUTH_EXPIRED"
        ? "Your token has expired. Please sign in again."
        : "Failed to send your question. Please try again.";
      updateConversation(idx, (c) => ({
        ...c,
        messages: c.messages.map((m) =>
          m.id === assistantMsg.id
            ? { ...m, content: message, genieStatus: { status: "FAILED", error: message, text: null, description: null, sql: null, statement_id: null, attachment_id: null, result: null, tables_used: [], suggested_questions: [] } }
            : m
        ),
      }));
      if (err instanceof Error && err.message === "AUTH_EXPIRED") {
        setHasToken(false);
      }
    }
  }, [activeIdx, conversations, updateConversation, scrollToBottom]);

  const handleNewChat = useCallback(() => {
    setActiveIdx(null);
    setPolling(false);
    setSidebarOpen(false);
    if (pollRef.current) clearTimeout(pollRef.current);
  }, []);

  const handleSelectConversation = useCallback((id: string) => {
    const idx = conversations.findIndex((c) => c.id === id);
    if (idx >= 0) { setActiveIdx(idx); setSidebarOpen(false); }
  }, [conversations]);

  const handleSignOut = useCallback(() => {
    clearToken();
    setHasToken(false);
    setSpaceInfo(null);
    setConversations([]);
    setActiveIdx(null);
    setSidebarOpen(false);
  }, []);

  if (!hasToken) {
    return (
      <div className="layout">
        <TokenPrompt onReady={() => setHasToken(true)} />
      </div>
    );
  }

  const isNewChat = active === null || active.messages.length === 0;
  const lastAssistant = active?.messages.filter((m) => m.role === "assistant").at(-1);
  const isWorking = polling && lastAssistant && !lastAssistant.genieStatus;

  return (
    <div className="layout">
      {/* Mobile sidebar overlay */}
      <div className={`sidebar-overlay ${sidebarOpen ? "open" : ""}`} onClick={() => setSidebarOpen(false)} />
      <Sidebar
        conversations={conversations}
        activeId={active?.id ?? null}
        onNewChat={handleNewChat}
        onSelect={handleSelectConversation}
        onSignOut={handleSignOut}
        onOpenSpace={() => setSpaceModalOpen(true)}
        spaceInfo={spaceInfo}
        className={sidebarOpen ? "open" : ""}
      />

      <main className="main-area">
        {/* Mobile header */}
        <div className="mobile-header">
          <button aria-label="Open chats" onClick={() => setSidebarOpen(true)}
            style={{ width: 44, height: 44, border: 0, background: "transparent" }}>
            <MenuIcon />
          </button>
          <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", alignItems: "center" }}>
            <span className="title">{active?.title ?? "New chat"}</span>
            <span className="meta">{spaceInfo?.space_name ?? "Genie"}</span>
          </div>
          <button aria-label="New chat" onClick={handleNewChat}
            style={{ width: 44, height: 44, border: 0, background: "transparent" }}>
            <PlusIcon />
          </button>
        </div>

        {isNewChat ? (
          <>
            <NewChat onAsk={handleAsk} spaceInfo={spaceInfo} />
            <Composer onSend={handleAsk} />
          </>
        ) : (
          <>
            <header className="main-header">
              <h1>{active?.title}</h1>
              <span className="space-badge">{spaceInfo?.space_name ?? "Genie"}</span>
            </header>

            <div className="main-content">
              {active?.messages.map((msg) => {
                if (msg.role === "user") {
                  return <div key={msg.id} className="user-bubble">{msg.content}</div>;
                }

                // Assistant message — could be working or done
                const gs = msg.genieStatus;
                if (!gs) {
                  // Still working
                  return (
                    <div key={msg.id} className="assistant-block">
                      <div className="icon-box"><DbIcon /></div>
                      <WorkingState status={currentGenieStatus} tablesUsed={currentTablesUsed} />
                    </div>
                  );
                }

                // Completed or failed
                const elapsed = msg.startedAt && msg.completedAt
                  ? ((msg.completedAt - msg.startedAt) / 1000).toFixed(1)
                  : null;

                return (
                  <div key={msg.id} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                    {gs.status !== "FAILED" && (
                      <div className="assistant-block">
                        <div className="icon-box"><DbIcon /></div>
                        <div className="assistant-body">
                          {gs.text && <div className="markdown-body"><Markdown>{gs.text}</Markdown></div>}
                          {gs.description && (
                            <div className="genie-note">
                              <strong>How Genie read this:</strong> {gs.description}
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    <ResultCard gs={gs} elapsed={elapsed} onRetry={() => handleAsk(msg.content || active?.messages.find(m => m.role === "user")?.content || "")} />

                    {/* Suggested follow-ups */}
                    {gs.suggested_questions.length > 0 && (
                      <div className="suggestions">
                        <span className="label">Genie suggests</span>
                        {gs.suggested_questions.map((q) => (
                          <button key={q} className="suggestion-chip" onClick={() => handleAsk(q)}>
                            {q}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
              <div ref={messagesEndRef} />
            </div>

            <Composer
              onSend={handleAsk}
              disabled={polling}
              placeholder={polling ? "Waiting for Genie to finish" : "Ask a follow-up"}
            />
          </>
        )}
      </main>

      {spaceModalOpen && spaceInfo && (
        <SpaceModal spaceInfo={spaceInfo} onClose={() => setSpaceModalOpen(false)} />
      )}
    </div>
  );
}
