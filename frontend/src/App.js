import React, { useState, useEffect } from "react";
import Upload from "./components/Upload";
import Query from "./components/Query";
import Documents from "./components/Documents";
import Guardrails from "./components/Guardrails";
import "./App.css";

const API = "http://localhost:8000";

export default function App() {
  const [activeTab, setActiveTab] = useState("query");
  const [apiReady, setApiReady] = useState(false);
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    fetch(`${API}/health`).then(r => r.json()).then(d => setApiReady(d.api_key_configured)).catch(() => setApiReady(false));
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const tabs = [
    { id: "upload",     label: "Upload",    icon: "upload",    desc: "Index Documents" },
    { id: "query",      label: "Research",  icon: "research",  desc: "Generate Reports" },
    { id: "documents",  label: "Library",   icon: "library",   desc: "Manage Knowledge" },
    { id: "guardrails", label: "Security",  icon: "security",  desc: "Threat Monitor" },
  ];

  return (
    <div className="shell">
      {/* Ambient background */}
      <div className="ambient">
        <div className="orb orb-1" />
        <div className="orb orb-2" />
        <div className="orb orb-3" />
        <div className="grid-overlay" />
      </div>

      {/* Sidebar */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <span className="brand-e">E</span><span className="brand-ra">RA</span>
          </div>
          <div className="brand-text">
            <span className="brand-name">Enterprise</span>
            <span className="brand-tagline">Research Assistant</span>
          </div>
        </div>

        <div className="nav-section-label">NAVIGATION</div>
        <nav className="nav">
          {tabs.map((tab, i) => (
            <button
              key={tab.id}
              className={`nav-btn ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
              style={{ animationDelay: `${i * 60}ms` }}
            >
              <NavIcon name={tab.icon} />
              <div className="nav-btn-text">
                <span className="nav-btn-label">{tab.label}</span>
                <span className="nav-btn-desc">{tab.desc}</span>
              </div>
              {activeTab === tab.id && <div className="nav-active-bar" />}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="sys-status">
            <div className={`sys-dot ${apiReady ? "live" : "offline"}`} />
            <span className="sys-label">{apiReady ? "System Live" : "Configure .env"}</span>
          </div>
          <div className="sys-clock">{time.toLocaleTimeString()}</div>
          <div className="sys-stack">
            <span>RAG · FlashRank · GPT-4o-mini</span>
            <span>MCA Final Project v2.0</span>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="main">
        <header className="topbar">
          <div className="topbar-left">
            <div className="breadcrumb">
              <span className="breadcrumb-root">ERA</span>
              <span className="breadcrumb-sep">›</span>
              <span className="breadcrumb-current">{tabs.find(t => t.id === activeTab)?.label}</span>
            </div>
            <h1 className="topbar-title">{tabs.find(t => t.id === activeTab)?.desc}</h1>
          </div>
          <div className="topbar-right">
            <div className="pipeline-badge">
              <span>Vector Search</span><span className="pipe-arrow">→</span>
              <span>FlashRank</span><span className="pipe-arrow">→</span>
              <span>CoT</span><span className="pipe-arrow">→</span>
              <span>GPT-4o</span>
            </div>
            <div className={`status-pill ${apiReady ? "ok" : "warn"}`}>
              <div className="status-dot-inner" />
              {apiReady ? "Connected" : "Offline"}
            </div>
          </div>
        </header>

        <div className="content">
          <div className="page-anim" key={activeTab}>
            {activeTab === "upload"     && <Upload />}
            {activeTab === "query"      && <Query />}
            {activeTab === "documents"  && <Documents />}
            {activeTab === "guardrails" && <Guardrails />}
          </div>
        </div>
      </main>
    </div>
  );
}

function NavIcon({ name }) {
  const icons = {
    upload: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>,
    research: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/><path d="M11 8v6M8 11h6"/></svg>,
    library: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>,
    security: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>,
  };
  return <span className="nav-icon-svg">{icons[name]}</span>;
}
